from django.urls import path

from .views import (
    AddCartItemView,
    CartView,
)

urlpatterns = [
    path(
        "",
        CartView.as_view(),
    ),

    path(
        "items/",
        AddCartItemView.as_view(),
    ),
]
