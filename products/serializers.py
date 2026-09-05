from rest_framework import serializers

from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
        ]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


class ProductSerializer(serializers.ModelSerializer):

    category = CategorySerializer(
        read_only=True
    )
    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "images",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        ]