# Migration eslatma

## discount_percent ustuni

`apps/products/models.py` da `discount_percent` `@property` dan DB ustuniga o'zgartirildi.

### Yangi loyiha uchun:
```bash
python manage.py makemigrations products
python manage.py migrate
```

### Mavjud loyiha uchun (ma'lumotlarni saqlash):
```bash
python manage.py makemigrations products --name add_discount_percent_field
python manage.py migrate
# Barcha mavjud mahsulotlarni yangilash:
python manage.py shell -c "
from apps.products.models import Product
for p in Product.objects.all():
    p.save()  # save() discount_percent ni hisoblaydi
print('Tugadi')
"
```
