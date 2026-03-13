from rest_framework import serializers
from .models import User, Address
from apps.products.models import Wishlist
from django.contrib.auth import authenticate


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ["email", "full_name", "phone", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Parollar mos kelmadi"})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"].lower(), password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Email yoki parol noto'g'ri"})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Hisob faol emas"})
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["id", "email", "full_name", "phone", "avatar", "is_verified", "created_at"]
        read_only_fields = ["id", "email", "is_verified", "created_at"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = ["id", "user", "title", "city", "district", "street", "extra_info", "is_default"]
        read_only_fields = ["id", "user"]


class WishlistSerializer(serializers.ModelSerializer):
    # ProductListSerializer ni lazy import qilib circular import dan qochamiz
    product = serializers.SerializerMethodField()

    class Meta:
        model  = Wishlist
        fields = ["id", "product", "created_at"]

    def get_product(self, obj):
        from apps.products.serializers import ProductListSerializer
        return ProductListSerializer(obj.product, context=self.context).data