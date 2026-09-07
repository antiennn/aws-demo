import logging

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductImageSerializer

logger = logging.getLogger(__name__)


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(
        is_active=True
    )
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(
        is_active=True
    )
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


class ProductImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request, product_id):

        try:
            product = Product.objects.get(
                id=product_id
            )
        except Product.DoesNotExist:
            return Response(
                {
                    "detail": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        image = request.FILES.get("image")

        if not image:
            return Response(
                {
                    "detail": "Image is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_image = ProductImage.objects.create(
            product=product,
            image=image,
        )

        serializer = ProductImageSerializer(
            product_image
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

class ProductImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request, product_id):

        try:
            print("=== PRODUCT IMAGE UPLOAD ===", flush=True)
            print("Product ID:", product_id, flush=True)
            print("FILES:", request.FILES, flush=True)

            product = Product.objects.get(
                id=product_id
            )

            image = request.FILES.get("image")

            if not image:
                return Response(
                    {
                        "detail": "Image is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            print("Image name:", image.name, flush=True)
            print("Image size:", image.size, flush=True)
            print("Image content type:", image.content_type, flush=True)

            product_image = ProductImage.objects.create(
                product=product,
                image=image,
            )

            print(
                "ProductImage created:",
                product_image.id,
                flush=True
            )

            serializer = ProductImageSerializer(
                product_image
            )

            print("Serializer data:", serializer.data, flush=True)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        except Product.DoesNotExist:
            return Response(
                {
                    "detail": "Product not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception:
            logger.exception(
                "PRODUCT IMAGE UPLOAD FAILED - product_id=%s",
                product_id,
            )
            raise