from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductAttribute, Review, Wishlist


class ProductImageInline(admin.TabularInline):
    model          = ProductImage
    extra          = 1
    fields         = ["image_preview", "image", "alt_text", "is_primary", "order"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;'
                'border-radius:8px;border:1px solid #e8e6e0;" />',
                obj.image.url
            )
        return "—"
    image_preview.short_description = "Ko'rinish"


class ProductAttributeInline(admin.TabularInline):
    model  = ProductAttribute
    extra  = 2
    fields = ["name", "value"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ["name", "slug", "parent", "product_count", "is_active", "order"]
    list_editable       = ["is_active", "order"]
    list_filter         = ["is_active", "parent"]
    search_fields       = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering            = ["order", "name"]

    def product_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        return format_html('<b style="color:#f97316">{}</b>', count)
    product_count.short_description = "Mahsulotlar"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = ["name", "category", "price_display", "discount_display",
                           "stock", "stock_display", "rating_avg", "is_active", "created_at"]
    list_filter         = ["is_active", "category", "created_at"]
    search_fields       = ["name", "description", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable       = ["is_active", "stock"]
    inlines             = [ProductImageInline, ProductAttributeInline]
    readonly_fields     = ["rating_avg", "review_count", "created_at", "updated_at"]
    list_per_page       = 25
    date_hierarchy      = "created_at"

    fieldsets = (
        ("Asosiy",       {"fields": ("name", "slug", "category", "description")}),
        ("Narx va stok", {"fields": ("price", "discount_price", "stock")}),
        ("Holat",        {"fields": ("is_active", "rating_avg", "review_count")}),
        ("Vaqt",         {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def price_display(self, obj):
        return format_html("{} som", "{:,}".format(int(obj.price)))
    price_display.short_description   = "Narx"
    price_display.admin_order_field   = "price"

    def discount_display(self, obj):
        if obj.discount_price:
            pct = obj.discount_percent
            return format_html('<b style="color:#22c55e">-{}%</b>', pct)
        return format_html('<span style="color:#ccc">-</span>')
    discount_display.short_description = "Chegirma"

    def stock_display(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:#ef4444;font-weight:700">Tugagan</span>')
        elif obj.stock < 5:
            return format_html('<span style="color:#f97316;font-weight:700">{}ta (!)</span>', obj.stock)
        return format_html('<span style="color:#22c55e;font-weight:700">OK</span>')
    stock_display.short_description = "Stok holat"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display    = ["product", "user", "rating", "short_comment", "created_at"]
    list_filter     = ["rating", "created_at"]
    search_fields   = ["product__name", "user__email", "comment"]
    readonly_fields = ["product", "user", "rating", "comment", "created_at"]

    def short_comment(self, obj):
        return obj.comment[:60] + "..." if len(obj.comment) > 60 else obj.comment
    short_comment.short_description = "Sharh"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display  = ["user_display", "product_display", "created_at"]
    list_filter   = ["created_at"]
    search_fields = ["user__email", "user__full_name", "product__name"]
    raw_id_fields = ["user", "product"]
    list_per_page = 25

    def user_display(self, obj):
        from django.utils.html import format_html
        return format_html("<b>{}</b>", obj.user.full_name)
    user_display.short_description = "Foydalanuvchi"

    def product_display(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a href="/admin/products/product/{}/change/">{}</a>',
            obj.product.id, obj.product.name
        )
    product_display.short_description = "Mahsulot"
