from django.utils import timezone
from .throttles import LoginThrottle, RegisterThrottle
from rest_framework.throttling import AnonRateThrottle
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import Address
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, AddressSerializer
import logging

logger = logging.getLogger(__name__)


class LoginThrottle(ScopedRateThrottle):
    scope = "login"

class RegisterThrottle(ScopedRateThrottle):
    scope = "register"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user    = serializer.save()
        refresh = RefreshToken.for_user(user)
        logger.info(f"Yangi foydalanuvchi: {user.email}")
        return Response({
            "user":    UserSerializer(user).data,
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        refresh = RefreshToken.for_user(user)
        return Response({
            "user":    UserSerializer(user).data,
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    """Refresh tokenni blacklist ga qo'shish"""
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "refresh token majburiy"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        pass  # token allaqachon bekor — muammo emas
    return Response({"success": True}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    old_password = request.data.get("old_password", "")
    new_password = request.data.get("new_password", "")

    if not old_password or not new_password:
        return Response(
            {"error": "old_password va new_password majburiy"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if len(new_password) < 8:
        return Response(
            {"error": "Yangi parol kamida 8 ta belgidan iborat bo'lishi kerak"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not request.user.check_password(old_password):
        return Response(
            {"error": "Eski parol noto'g'ri"},
            status=status.HTTP_400_BAD_REQUEST
        )

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    logger.info(f"Parol o'zgartirildi: {request.user.email}")
    return Response({"success": True, "message": "Parol muvaffaqiyatli o'zgartirildi"})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user


class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class   = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by("-is_default", "id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


# ── Wishlist ──────────────────────────────────────────────────────
from apps.products.models import Wishlist
from .serializers import WishlistSerializer
from apps.products.models import Product as _Product


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wishlist_view(request):
    """Sevimlilar ro'yxati"""
    items = Wishlist.objects.filter(user=request.user).select_related("product__category").prefetch_related("product__images")
    return Response(WishlistSerializer(items, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def wishlist_toggle_view(request, product_id):
    """Mahsulotni sevimlilarga qo'shish / o'chirish (toggle)"""
    try:
        product = _Product.objects.get(id=product_id, is_active=True)
    except _Product.DoesNotExist:
        return Response({"error": "Mahsulot topilmadi"}, status=404)

    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        return Response({"action": "removed", "product_id": str(product_id)})
    return Response({"action": "added", "product_id": str(product_id)}, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def wishlist_clear_view(request):
    """Barcha sevimlillarni o'chirish"""
    count, _ = Wishlist.objects.filter(user=request.user).delete()
    return Response({"deleted": count})


# ── Email tekshirish ──────────────────────────────────────────────
import hashlib, hmac

def _make_verify_token(user_id: str, secret: str) -> str:
    return hmac.new(secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_verify_email_view(request):
    """Email tasdiqlash havolasini yuborish"""
    from django.conf import settings
    from django.core.mail import send_mail

    user = request.user
    if user.is_verified:
        return Response({"message": "Email allaqachon tasdiqlangan"})

    token = _make_verify_token(str(user.id), settings.SECRET_KEY)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}&uid={user.id}"

    send_mail(
        subject="UzBox — Email tasdiqlash",
        message=f"Email tasdiqlash uchun quyidagi havolani bosing:\n{verify_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    logger.info(f"Verify email yuborildi: {user.email}")
    return Response({"message": "Email yuborildi. Pochta qutingizni tekshiring."})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_view(request):
    """
    POST /api/auth/verify-email/
    Body: {"uid": "uuid", "token": "sha256hex"}
    """
    from django.conf import settings

    uid   = request.data.get("uid", "")
    token = request.data.get("token", "")

    if not uid or not token:
        return Response({"error": "uid va token majburiy"}, status=400)

    from .models import User
    try:
        user = User.objects.get(id=uid)
    except (User.DoesNotExist, Exception):
        return Response({"error": "Foydalanuvchi topilmadi"}, status=404)

    expected = _make_verify_token(str(user.id), settings.SECRET_KEY)
    if not hmac.compare_digest(expected, token):
        return Response({"error": "Token noto\'g\'ri"}, status=400)

    user.is_verified = True
    user.save(update_fields=["is_verified"])
    return Response({"message": "Email muvaffaqiyatli tasdiqlandi!"})