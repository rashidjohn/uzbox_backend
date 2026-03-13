from .cloudinary_utils import get_product_image_url, get_thumbnail_url
from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductAttribute, Review


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ["id", "name", "slug", "image", "parent", "children"]

    def get_children(self, obj):
        # prefetch_related("children") bilan N+1 yo'q
        children = [c for c in obj.children.all() if c.is_active]
        return CategorySerializer(children, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductAttribute
        fields = ["name", "value"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model  = Review
        fields = ["id", "user_name", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user_name", "created_at"]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Reyting 1 dan 5 gacha bo'lishi kerak")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model  = Product
        fields = [
            "id", "name", "slug", "category_name",
            "price", "discount_price", "discount_percent",
            "current_price", "stock", "rating_avg",
            "review_count", "primary_image",
        ]
        read_only_fields = ["discount_percent"]

    def get_primary_image(self, obj):
        # prefetch_related("images") bilan ishlaydi
        images = obj.images.all()
        img = next((i for i in images if i.is_primary), None) or (images[0] if images else None)
        raw = img.image.url if img else None
        return get_thumbnail_url(raw) if raw else None

class ProductDetailSerializer(serializers.ModelSerializer):
    images     = ProductImageSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    reviews    = ReviewSerializer(many=True, read_only=True)
    category   = CategorySerializer(read_only=True)

    class Meta:
        model  = Product
        fields = [
            "id", "name", "slug", "description", "category",
            "price", "discount_price", "discount_percent", "current_price",
            "stock", "rating_avg", "review_count",
            "images", "attributes", "reviews", "created_at",
        ]
