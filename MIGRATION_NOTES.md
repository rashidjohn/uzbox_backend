# Yangi migratsiyalar kerak

## Buyruqlar (tartibda bajaring):

```bash
cd backend

# 1. Yangi fieldlar uchun migrations yaratish
python manage.py makemigrations

# 2. Migratsiyalarni ko'rish (tekshirish)
python manage.py showmigrations

# 3. Tatbiq etish
python manage.py migrate
```

## Yangi DB o'zgarishlari:

### `apps/products/migrations/`
- `Product.discount_percent` — property → DB ustuni (`PositiveIntegerField`)
- Eski ma'lumotlar uchun:
  ```bash
  python manage.py shell -c "
  from apps.products.models import Product
  for p in Product.objects.all():
      p.save(update_fields=['discount_percent'])
  print('✅ discount_percent yangilandi')
  "
  ```

### `apps/users/migrations/`
- `Wishlist` modeli — yangi jadval

### `apps/orders/migrations/`
- `Order.promo_code` — CharField
- `Order.discount_amount` — DecimalField
- `PromoCode` modeli (promo.py) — alohida migrate kerak:
  ```bash
  # promo.py ni orders/models.py ga import qilish yoki:
  python manage.py makemigrations orders --name="add_promo_code"
  ```

## Muhim eslatma:
PromoCode va Wishlist modellari INSTALLED_APPS da allaqachon bor apps orqali taniladi.
Faqat `makemigrations` va `migrate` yetarli.
