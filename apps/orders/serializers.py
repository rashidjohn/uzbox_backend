from django.db import transaction
from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer

ADDRESS_REQUIRED_FIELDS = ["full_name", "phone", "city", "district", "street"]


class OrderItemSerializer(serializers.ModelSerializer):
    product    = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    subtotal   = serializers.ReadOnlyField()

    class Meta:
        model  = OrderItem
        fields = ["id", "product", "product_id", "quantity", "price", "subtotal"]
        read_only_fields = ["price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model  = Order
        fields = ["id", "status", "total_price", "payment_method",
                  "address", "note", "promo_code", "discount_amount",
                  "guest_email", "items", "created_at"]
        read_only_fields = ["id", "status", "total_price", "discount_amount", "created_at"]
        extra_kwargs     = {"guest_email": {"required": False}}

    def validate_address(self, value):
        """Manzil majburiy maydonlarini tekshirish"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Manzil to'g'ri formatda bo'lishi kerak")
        missing = [f for f in ADDRESS_REQUIRED_FIELDS if not str(value.get(f, "")).strip()]
        if missing:
            raise serializers.ValidationError(
                f"Majburiy maydonlar to'ldirilmagan: {', '.join(missing)}"
            )
        return value

    def validate_items(self, items_data):
        if not items_data:
            raise serializers.ValidationError("Kamida 1 ta mahsulot bo'lishi shart")
        errors = []
        for item in items_data:
            try:
                product = Product.objects.get(id=item["product_id"], is_active=True)
            except Product.DoesNotExist:
                errors.append(f"Mahsulot topilmadi: {item['product_id']}")
                continue
            if product.stock < item["quantity"]:
                errors.append(f"{product.name}: stokda faqat {product.stock} ta bor")
        if errors:
            raise serializers.ValidationError(errors)
        return items_data

    @transaction.atomic
    def create(self, validated_data):
        # Promo-kod tekshirish va chegirma hisoblash
        promo_code_str  = validated_data.pop("promo_code", "").strip().upper()
        discount_amount = 0
        items_data  = validated_data.pop("items")
        product_ids = [i["product_id"] for i in items_data]

        # select_for_update — race condition yo'q
        products = {
            p.id: p for p in
            Product.objects.filter(id__in=product_ids).select_for_update()
        }

        # Stok qayta tekshirish (lock olingandan keyin)
        errors = []
        for item_data in items_data:
            product = products.get(item_data["product_id"])
            if not product:
                errors.append(f"Mahsulot topilmadi: {item_data['product_id']}")
            elif product.stock < item_data["quantity"]:
                errors.append(f"{product.name}: stokda faqat {product.stock} ta bor")
        if errors:
            raise serializers.ValidationError({"items": errors})

        order = Order.objects.create(**validated_data, total_price=0)

        total       = 0
        order_items = []
        for item_data in items_data:
            product = products[item_data["product_id"]]
            price   = product.current_price
            order_items.append(OrderItem(
                order=order,
                product=product,
                quantity=item_data["quantity"],
                price=price,
            ))
            total         += price * item_data["quantity"]
            product.stock -= item_data["quantity"]

        OrderItem.objects.bulk_create(order_items)

        for product in products.values():
            product.save(update_fields=["stock"])

        # Promo-kod chegirma qo'llash
        if promo_code_str:
            try:
                from .promo import PromoCode
                promo = PromoCode.objects.get(code__iexact=promo_code_str)
                valid, _ = promo.is_valid(float(total))
                if valid:
                    discount_amount = promo.calculate_discount(float(total))
                    promo.used_count += 1
                    promo.save(update_fields=["used_count"])
            except Exception:
                pass

        order.total_price    = max(0, float(total) - float(discount_amount))
        order.promo_code     = promo_code_str
        order.discount_amount = discount_amount
        order.save(update_fields=["total_price", "promo_code", "discount_amount"])
        return order
