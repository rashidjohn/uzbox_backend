from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ["avatar_thumbnail", "email", "full_name", "phone",
                       "is_verified_badge", "is_active", "is_staff", "created_at"]
    list_filter     = ["is_verified", "is_staff", "is_active", "created_at"]
    search_fields   = ["email", "full_name", "phone"]
    ordering        = ["-created_at"]
    list_per_page   = 25
    date_hierarchy  = "created_at"

    fieldsets = (
        ("Kirish ma'lumotlari", {
            "fields": ("email", "password"),
            "description": "Foydalanuvchi email va paroli",
        }),
        ("Shaxsiy ma'lumotlar", {
            "fields": ("full_name", "phone", "avatar", "avatar_preview"),
        }),
        ("Ruxsatlar", {
            "fields": ("is_active", "is_staff", "is_superuser", "is_verified",
                       "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        ("Faollik", {
            "fields": ("last_login", "created_at"),
            "classes": ("collapse",),
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "full_name", "phone", "password1", "password2"),
        }),
    )
    readonly_fields = ["last_login", "created_at", "avatar_preview"]

    # ── Avatar thumbnail (ro'yxatda) ────────────────────────
    def avatar_thumbnail(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;'
                'object-fit:cover;border:2px solid #f97316;" />',
                obj.avatar.url
            )
        initials = "".join([w[0].upper() for w in obj.full_name.split()[:2]]) or "?"
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:'
            'linear-gradient(135deg,#f97316,#ea580c);display:flex;align-items:center;'
            'justify-content:center;color:white;font-weight:700;font-size:13px;">{}</div>',
            initials
        )
    avatar_thumbnail.short_description = ""

    # ── Avatar katta ko'rinish (tahrirlashda) ───────────────
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:100px;height:100px;border-radius:50%;'
                'object-fit:cover;border:3px solid #f97316;display:block;margin-bottom:8px;" />'
                '<small style="color:#6b6b60;">Rasmni o\'zgartirish uchun yuqoridagi '
                '<b>Avatar</b> maydonidan yangi rasm tanlang</small>',
                obj.avatar.url
            )
        return format_html(
            '<div style="width:100px;height:100px;border-radius:50%;background:#f5f4f0;'
            'display:flex;align-items:center;justify-content:center;font-size:36px;'
            'margin-bottom:8px;">👤</div>'
            '<small style="color:#6b6b60;">Rasm yuklanmagan</small>'
        )
    avatar_preview.short_description = "Joriy rasm"

    # ── Verified badge ──────────────────────────────────────
    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background:#dcfce7;color:#15803d;padding:2px 10px;'
                'border-radius:100px;font-size:11px;font-weight:700;">✓ Tasdiqlangan</span>'
            )
        return format_html(
            '<span style="background:#fef2f2;color:#dc2626;padding:2px 10px;'
            'border-radius:100px;font-size:11px;font-weight:700;">✗ Tasdiqlanmagan</span>'
        )
    is_verified_badge.short_description = "Holat"
    is_verified_badge.admin_order_field = "is_verified"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ["user_display", "title", "city", "district", "street", "is_default"]
    list_filter   = ["city", "is_default"]
    search_fields = ["user__email", "user__full_name", "city", "district", "street"]
    list_per_page = 25

    def user_display(self, obj):
        return format_html(
            '<b>{}</b><br><small style="color:#9a9a90">{}</small>',
            obj.user.full_name, obj.user.email
        )
    user_display.short_description = "Foydalanuvchi"
