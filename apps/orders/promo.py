"""Promo-kod modeli va validator"""
import uuid
from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    TYPE_CHOICES = [
        ("percent", "Foiz"),
        ("fixed",   "Soliqlangan"),
    ]
    code            = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type   = models.CharField(max_length=10, choices=TYPE_CHOICES, default="percent")
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_uses        = models.PositiveIntegerField(default=0, help_text="0 = cheksiz")
    used_count      = models.PositiveIntegerField(default=0)
    valid_from      = models.DateTimeField(default=timezone.now)
    valid_until     = models.DateTimeField(null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Promo-kod"
        verbose_name_plural = "Promo-kodlar"

    def __str__(self):
        return f"{self.code} ({self.discount_type}: {self.discount_value})"

    def is_valid(self, order_total=0):
        now = timezone.now()
        if not self.is_active:
            return False, "Promo-kod faol emas"
        if self.valid_until and now > self.valid_until:
            return False, "Promo-kod muddati o'tgan"
        if now < self.valid_from:
            return False, "Promo-kod hali faol emas"
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "Promo-kod limiti tugagan"
        if order_total < float(self.min_order_price):
            return False, f"Minimal buyurtma: {self.min_order_price:,.0f} so'm"
        return True, "OK"

    def calculate_discount(self, order_total):
        if self.discount_type == "percent":
            return round(order_total * float(self.discount_value) / 100, 2)
        return min(float(self.discount_value), order_total)
