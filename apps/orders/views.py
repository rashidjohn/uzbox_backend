from apps.users.throttles import CheckoutThrottle
import logging
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Order
from .serializers import OrderSerializer

logger = logging.getLogger(__name__)


class OrderPagination(PageNumberPagination):
    page_size            = 10
    page_size_query_param = "page_size"
    max_page_size        = 50


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class   = OrderSerializer
    pagination_class   = OrderPagination

    throttle_classes = [CheckoutThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return []  # Guest checkout — hamma buyurtma bera oladi
        return [IsAuthenticated()]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items__product__images")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        # Login qilgan bo'lsa user, aks holda guest_email
        if self.request.user.is_authenticated:
            order = serializer.save(user=self.request.user)
        else:
            guest_email = self.request.data.get("guest_email", "")
            if not guest_email:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"guest_email": "Guest sifatida buyurtma berish uchun email majburiy"})
            order = serializer.save(user=None, guest_email=guest_email)
        try:
            from apps.notifications.tasks import send_order_confirmation
            send_order_confirmation.delay(str(order.id))
        except Exception as e:
            logger.error(f"Celery task xatosi: {e}")


class OrderDetailView(generics.RetrieveUpdateAPIView):
    http_method_names  = ["get", "patch", "head", "options"]
    serializer_class   = OrderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return (
                Order.objects
                .filter(user=self.request.user)
                .prefetch_related("items__product__images")
            )
        # Guest fallback
        return Order.objects.filter(user__isnull=True).prefetch_related("items__product__images")

    def get_object(self):
        obj = super().get_object()
        if not self.request.user.is_authenticated:
            guest_email = self.request.query_params.get("guest_email") or self.request.data.get("guest_email")
            if not guest_email or obj.guest_email != guest_email:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Siz ushbu buyurtmani ko'rish huquqiga ega emassiz. To'g'ri guest_email kiriting.")
        return obj

    def perform_update(self, serializer):
        new_status = self.request.data.get("status")
        order      = self.get_object()
        if new_status and new_status != "cancelled":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Faqat 'cancelled' statusini o'zgartirishingiz mumkin")
        if new_status == "cancelled" and order.status not in ("pending",):
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError({"status": "Faqat kutilayotgan buyurtmani bekor qilish mumkin"})
        instance = serializer.save()
        # status read_only — to'g'ridan saqlaymiz
        if new_status == "cancelled":
            instance.status = "cancelled"
            instance.save(update_fields=["status"])
            try:
                from apps.notifications.tasks import send_order_status_update
                send_order_status_update.delay(str(instance.id), "cancelled")
            except Exception as e:
                logger.error(f"Celery task xatosi: {e}")