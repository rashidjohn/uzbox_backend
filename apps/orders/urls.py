from django.urls import path
from .views import OrderListCreateView, OrderDetailView
from .promo_views import check_promo_view

urlpatterns = [
    path("",              OrderListCreateView.as_view(), name="orders"),
    path("<uuid:pk>/",    OrderDetailView.as_view(),     name="order_detail"),
    path("promo/check/",  check_promo_view,              name="promo_check"),
]
