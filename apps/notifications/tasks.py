import logging
from config.celery import app  # type: ignore
from django.core.mail import send_mail  # type: ignore
from django.conf import settings  # type: ignore

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation(self, order_id: str):
    try:
        from apps.orders.models import Order  # type: ignore
        order = (
            Order.objects
            .select_related("user")
            .prefetch_related("items__product")
            .get(id=order_id)
        )
        items_text = "\n".join([
            f"  - {item.product.name} x{item.quantity} = {float(item.subtotal):,.0f} som"
            for item in order.items.all()
        ])
        send_mail(
            subject=f"Buyurtmangiz qabul qilindi #{str(order.id).split('-')[0].upper()}",
            message=(
                f"Hurmatli {order.user.full_name if order.user else 'Mijoz'},\n\n"
                f"Buyurtmangiz muvaffaqiyatli qabul qilindi!\n\n"
                f"Buyurtma: #{str(order.id).split('-')[0].upper()}\n"
                f"Holati: {order.get_status_display()}\n\n"
                f"Mahsulotlar:\n{items_text}\n\n"
                f"Jami: {float(order.total_price):,.0f} som\n\n"
                f"Rahmat, UzBox jamoasi"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email if order.user else order.guest_email],
            fail_silently=False,
        )
        logger.info(f"Email yuborildi: {order.user.email if order.user else order.guest_email}")
    except Exception as exc:
        from django.core.exceptions import ObjectDoesNotExist  # type: ignore
        if isinstance(exc, ObjectDoesNotExist):
            logger.error(f"Order topilmadi: {order_id}")
            return
        logger.error(f"Email xatosi {order_id}: {exc}")
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update(self, order_id: str, new_status: str):
    """Buyurtma statusi o'zgarganda email yuborish"""
    STATUS_MESSAGES = {
        "paid":       ("To'landi ✅",       "Buyurtmangiz uchun to'lov qabul qilindi. Tez orada tayyorlanamiz."),
        "processing": ("Tayyorlanmoqda 📦", "Buyurtmangiz tayyorlanmoqda. Kuting!"),
        "shipped":    ("Yo'lda 🚚",         "Buyurtmangiz jo'natildi. Yaqinda yetib boradi."),
        "delivered":  ("Yetkazildi 🎉",     "Buyurtmangiz muvaffaqiyatli yetkazildi. Xaridingiz muborak!"),
        "cancelled":  ("Bekor qilindi ❌",  "Buyurtmangiz bekor qilindi. Savollar uchun biz bilan bog'laning."),
    }
    if new_status not in STATUS_MESSAGES:
        return

    try:
        from apps.orders.models import Order  # type: ignore
        order = Order.objects.select_related("user").get(id=order_id)
        subject_suffix, body_text = STATUS_MESSAGES[new_status]

        send_mail(
            subject=f"Buyurtma #{str(order.id).split('-')[0].upper()} — {subject_suffix}",
            message=(
                f"Hurmatli {order.user.full_name if order.user else 'Mijoz'},\n\n"
                f"{body_text}\n\n"
                f"Buyurtma raqami: #{str(order.id).split('-')[0].upper()}\n"
                f"Jami: {float(order.total_price):,.0f} so'm\n\n"
                f"Rahmat, UzBox jamoasi"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email if order.user else order.guest_email],
            fail_silently=False,
        )
        logger.info(f"Status email: {order.user.email if order.user else order.guest_email} -> {new_status}")
    except Exception as exc:
        logger.error(f"Status email xatosi {order_id}: {exc}")
        raise self.retry(exc=exc)