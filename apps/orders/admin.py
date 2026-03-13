from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem

STATUS_COLORS = {
    "pending":    "#f59e0b",
    "paid":       "#6366f1",
    "processing": "#8b5cf6",
    "shipped":    "#0ea5e9",
    "delivered":  "#22c55e",
    "cancelled":  "#ef4444",
}
STATUS_LABELS = {
    "pending":    "Kutilmoqda",
    "paid":       "Tolandi",
    "processing": "Tayyorlanmoqda",
    "shipped":    "Yolda",
    "delivered":  "Yetkazildi",
    "cancelled":  "Bekor qilindi",
}


class OrderItemInline(admin.TabularInline):
    model          = OrderItem
    extra          = 0
    readonly_fields = ["product", "quantity", "price", "subtotal_display"]
    can_delete     = False

    def subtotal_display(self, obj):
        return format_html("<b>{} som</b>", "{:,}".format(int(obj.price * obj.quantity)))
    subtotal_display.short_description = "Jami"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ["short_id", "user_display", "status", "status_badge",
                       "total_display", "payment_method", "created_at"]
    list_filter     = ["status", "payment_method", "created_at"]
    search_fields   = ["user__email", "user__full_name"]
    list_editable   = ["status"]
    inlines         = [OrderItemInline]
    readonly_fields = ["id", "user", "total_price", "payment_id", "created_at"]
    list_per_page   = 25
    date_hierarchy  = "created_at"

    fieldsets = (
        ("Buyurtma", {"fields": ("id", "user", "status", "payment_method", "payment_id")}),
        ("Manzil",   {"fields": ("address",)}),
        ("Moliya",   {"fields": ("total_price",)}),
        ("Vaqt",     {"fields": ("created_at",)}),
    )


    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            old_status = Order.objects.get(pk=obj.pk).status
            super().save_model(request, obj, form, change)
            # Status o'zgarganda email
            if old_status != obj.status:
                try:
                    from apps.notifications.tasks import send_order_status_update
                    send_order_status_update.delay(str(obj.id), obj.status)
                except Exception:
                    pass
        else:
            super().save_model(request, obj, form, change)
    def short_id(self, obj):
        return format_html("<code>#{}</code>", str(obj.id)[:8].upper())
    short_id.short_description = "ID"

    def user_display(self, obj):
        return format_html("<b>{}</b><br><small>{}</small>", obj.user.full_name, obj.user.email)
    user_display.short_description = "Foydalanuvchi"

    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#9a9a90")
        label = STATUS_LABELS.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:100px;font-size:11px;font-weight:700">{}</span>',
            color, label
        )
    status_badge.short_description = "Badge"

    def total_display(self, obj):
        return format_html("<b>{} som</b>", "{:,}".format(int(obj.total_price)))
    total_display.short_description = "Summa"
    total_display.admin_order_field = "total_price"

# ── Promo-kod admin ──────────────────────────────────────────────
try:
    from .promo import PromoCode

    @admin.register(PromoCode)
    class PromoCodeAdmin(admin.ModelAdmin):
        list_display   = ["code", "discount_type", "discount_value", "min_order_price",
                          "used_count", "max_uses", "is_active", "valid_until"]
        list_filter    = ["discount_type", "is_active"]
        search_fields  = ["code"]
        list_editable  = ["is_active"]
        readonly_fields = ["used_count", "created_at"]
        fieldsets = (
            ("Kod",      {"fields": ("code", "is_active")}),
            ("Chegirma", {"fields": ("discount_type", "discount_value", "min_order_price")}),
            ("Limit",    {"fields": ("max_uses", "used_count", "valid_from", "valid_until")}),
            ("Vaqt",     {"fields": ("created_at",)}),
        )
except Exception:
    pass
