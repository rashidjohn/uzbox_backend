import uuid
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending",    "Kutilmoqda"),
        ("paid",       "Tolandi"),
        ("processing", "Jarayonda"),
        ("shipped",    "Yuborildi"),
        ("delivered",  "Yetkazildi"),
        ("cancelled",  "Bekor qilindi"),
    ]
    PAYMENT_CHOICES = [
        ("click", "Click"),
        ("payme", "Payme"),
        ("cash",  "Naqd"),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user           = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="orders", null=True, blank=True)
    guest_email    = models.EmailField(blank=True)  # Guest checkout uchun
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    total_price    = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="click", db_index=True)
    payment_id     = models.CharField(max_length=255, blank=True)
    address        = models.JSONField()
    note            = models.TextField(blank=True)
    promo_code      = models.CharField(max_length=50, blank=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"#{str(self.id)[:8].upper()} - {self.user.full_name} - {self.get_status_display()}"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product  = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price    = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


@receiver(pre_save, sender=Order)
def capture_previous_status(sender, instance, **kwargs):
    """
    Saqlashdan OLDIN DB dagi oldingi statusni yodlab qo'yamiz.
    update_fields=['status'] bilan ham to'g'ri ishlaydi.
    """
    if not instance.pk:
        instance._prev_status = None
        return
    try:
        instance._prev_status = (
            Order.objects.values_list("status", flat=True).get(pk=instance.pk)
        )
    except Order.DoesNotExist:
        instance._prev_status = None


@receiver(post_save, sender=Order)
def restore_stock_on_cancel(sender, instance, created, **kwargs):
    """Buyurtma bekor qilinganda stokni qaytarish"""
    if created:
        return
    prev = getattr(instance, "_prev_status", None)
    if prev != "cancelled" and instance.status == "cancelled":
        for item in instance.items.select_related("product"):
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=["stock"])


# PromoCode ni bu yerdan ham eksport — migration uchun
from .promo import PromoCode
__all__ = ["Order", "OrderItem", "PromoCode"]
