from apps.users.throttles import ReviewThrottle
import logging
from django.core.cache import cache
from django.db.models import Avg, Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from .models import Category, Product
from .serializers import (
    CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ReviewSerializer,
)
from .filters import ProductFilter

logger = logging.getLogger(__name__)


class CategoryListView(generics.ListAPIView):
    serializer_class   = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Category.objects
            .filter(is_active=True, parent=None)
            .prefetch_related("children")
        )


class ProductListView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [AllowAny]
    filterset_class    = ProductFilter
    search_fields      = ["name", "description", "category__name"]
    ordering_fields    = ["price", "created_at", "rating_avg", "discount_percent"]
    ordering           = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("images")
        )

    def get_paginator(self):
        if self.request.query_params.get("ids"):
            return None
        return super().get_paginator()

    def list(self, request, *args, **kwargs):
        if request.query_params.get("ids"):
            queryset   = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class   = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field       = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", "attributes", "reviews__user", "category__children")
        )

    def retrieve(self, request, *args, **kwargs):
        cache_key = f"product:{kwargs['slug']}"
        cached    = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=30)
        return response


class ReviewCreateView(generics.CreateAPIView):
    serializer_class   = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            product = Product.objects.get(slug=self.kwargs["slug"], is_active=True)
        except Product.DoesNotExist:
            raise NotFound("Mahsulot topilmadi")

        # Takroriy sharh — 400 qaytarish (IntegrityError emas)
        from .models import Review
        if Review.objects.filter(product=product, user=self.request.user).exists():
            raise ValidationError({"detail": "Siz bu mahsulotga allaqachon sharh qoldirgansiz"})

        serializer.save(user=self.request.user, product=product)

        stats = product.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        product.rating_avg   = round(stats["avg"] or 0, 1)
        product.review_count = stats["count"]
        product.save(update_fields=["rating_avg", "review_count"])

        cache.delete(f"product:{product.slug}")


class ProductAutocompleteView(generics.ListAPIView):
    """
    GET /api/products/autocomplete/?q=laptop
    Tez qidiruv — faqat nom va slug qaytaradi (5 ta max)
    """
    serializer_class   = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Product.objects.none()
        return (
            Product.objects
            .filter(name__icontains=q, is_active=True)
            .select_related("category")
            .prefetch_related("images")
            [:8]
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [{"id": str(p.id), "name": p.name, "slug": p.slug,
                 "price": p.current_price, "image": p.primary_image}
                for p in qs]
        return Response(data)
