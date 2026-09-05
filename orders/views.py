from django.db import transaction
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = (
            Cart.objects
            .prefetch_related("items__product")
            .get(user=request.user)
        )

        serializer = CartSerializer(cart)

        return Response(serializer.data)


class AddCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product")
        quantity = int(
            request.data.get("quantity", 1)
        )

        if quantity <= 0:
            return Response(
                {"detail": "Quantity must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True,
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart = Cart.objects.get(
            user=request.user
        )

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": quantity
            },
        )

        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])

        serializer = CartItemSerializer(item)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        orders = (
            Order.objects
            .filter(user=request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

        serializer = OrderSerializer(
            orders,
            many=True,
        )

        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):

        cart = (
            Cart.objects
            .select_for_update()
            .get(user=request.user)
        )

        cart_items = list(
            CartItem.objects
            .select_related("product")
            .filter(cart=cart)
            .order_by("product_id")
        )

        if not cart_items:
            return Response(
                {
                    "detail": "Cart is empty"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_ids = [
            item.product_id
            for item in cart_items
        ]

        locked_products = {
            product.id: product
            for product in (
                Product.objects
                .select_for_update()
                .filter(
                    id__in=product_ids,
                    is_active=True,
                )
            )
        }

        total_amount = 0

        for item in cart_items:

            product = locked_products.get(
                item.product_id
            )

            if product is None:
                return Response(
                    {
                        "detail": (
                            f"Product {item.product_id} "
                            "is no longer available"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if item.quantity > product.stock:
                return Response(
                    {
                        "detail": (
                            f"Not enough stock for "
                            f"{product.name}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total_amount += (
                    product.price * item.quantity
            )

        order = Order.objects.create(
            user=request.user,
            status=Order.Status.PENDING,
            total_amount=total_amount,
        )

        order_items = []

        for item in cart_items:
            product = locked_products[item.product_id]

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price,
                )
            )

            product.stock -= item.quantity

        OrderItem.objects.bulk_create(
            order_items
        )

        Product.objects.bulk_update(
            locked_products.values(),
            ["stock"],
        )

        CartItem.objects.filter(
            cart=cart
        ).delete()

        serializer = OrderSerializer(
            order
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items__product")
        )


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):

        try:
            order = (
                Order.objects
                .select_for_update()
                .get(
                    pk=pk,
                    user=request.user,
                )
            )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not order.can_transition_to(
                Order.Status.CANCELLED
        ):
            return Response(
                {
                    "detail": (
                        f"Order cannot be cancelled "
                        f"when status is '{order.status}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_items = list(
            OrderItem.objects
            .filter(order=order)
            .order_by("product_id")
        )

        product_ids = [
            item.product_id
            for item in order_items
        ]

        products = {
            product.id: product
            for product in (
                Product.objects
                .select_for_update()
                .filter(id__in=product_ids)
                .order_by("id")
            )
        }

        for item in order_items:
            product = products[item.product_id]

            product.stock += item.quantity

        Product.objects.bulk_update(
            products.values(),
            ["stock"],
        )

        order.status = Order.Status.CANCELLED

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        serializer = OrderSerializer(order)

        return Response(serializer.data)