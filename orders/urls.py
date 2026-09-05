from django.urls import path

from .views import OrderDetailView, CancelOrderView, OrderListCreateView

urlpatterns = [
    path(
        "",
        OrderListCreateView.as_view(),
    ),
    path(
        "<int:pk>/",
        OrderDetailView.as_view(),
    ),
    path(
        "<int:pk>/cancel/",
        CancelOrderView.as_view(),
    ),
]