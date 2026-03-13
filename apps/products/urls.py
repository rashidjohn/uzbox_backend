from django.urls import path
from .views import (
    CategoryListView, ProductListView, ProductDetailView,
    ReviewCreateView, ProductAutocompleteView,
)

urlpatterns = [
    path("",                       ProductListView.as_view(),       name="products"),
    path("categories/",            CategoryListView.as_view(),       name="categories"),
    path("autocomplete/",          ProductAutocompleteView.as_view(), name="autocomplete"),
    path("<slug:slug>/",           ProductDetailView.as_view(),      name="product_detail"),
    path("<slug:slug>/reviews/",   ReviewCreateView.as_view(),       name="create_review"),
]
