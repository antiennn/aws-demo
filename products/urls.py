from django.urls import path

from .views import (
    ProductDetailView,
    ProductListView, ProductImageUploadView,
)

urlpatterns = [
    path(
        "",
        ProductListView.as_view(),
    ),

    path(
        "<int:pk>/",
        ProductDetailView.as_view(),
    ),

    path(
        "<int:product_id>/images/",
        ProductImageUploadView.as_view(),
    ),
]