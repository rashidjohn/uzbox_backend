import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify


def unique_slugify(model_class, name, instance=None):
    """Noyob slug yaratish — xuddi shu nom bo'lsa raqam qo'shadi"""
    base_slug = slugify(name)
    if not base_slug:
        base_slug = str(uuid.uuid4())[:8]
    slug = base_slug
    counter = 2
    while True:
        qs = model_class.objects.filter(slug=slug)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if not qs.exists():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


class Category(models.Model):
    name      = models.CharField(max_length=200)
    slug      = models.SlugField(unique=True)
    parent    = models.ForeignKey(
        "self", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="children"
    )
    image     = models.ImageField(upload_to="categories/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order     = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name        = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering            = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(Category, self.name, self)
        super().save(*args, **kwargs)


class Product(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name             = models.CharField(max_length=500)
    slug             = models.SlugField(unique=True, max_length=550)
    description      = models.TextField()
    category         = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, related_name="products"
    )
    price            = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price   = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # DB ustuni — ordering uchun
    discount_percent = models.PositiveIntegerField(default=0, editable=False)
    stock            = models.PositiveIntegerField(default=0)
    is_active        = models.BooleanField(default=True)
    rating_avg       = models.FloatField(default=0.0)
    review_count     = models.PositiveIntegerField(default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering            = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def primary_image(self):
        """Asosiy rasm URL — admin da ko'rish uchun"""
        try:
            img = self.images.filter(is_primary=True).first() or self.images.first()
            return img.image.url if img else None
        except Exception:
            return None

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(Product, self.name, self)
        # discount_price price dan katta bo'lmasligi kerak
        if self.discount_price and self.discount_price >= self.price:
            self.discount_price = None
        # discount_percent ni DB ga yozish (sort uchun)
        if self.discount_price and self.price > 0:
            self.discount_percent = int((1 - self.discount_price / self.price) * 100)
        else:
            self.discount_percent = 0
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image      = models.ImageField(upload_to="products/")
    alt_text   = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    name    = models.CharField(max_length=100)
    value   = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}: {self.value}"


class Review(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user       = models.ForeignKey("users.User", on_delete=models.CASCADE)
    rating     = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["product", "user"]
        ordering        = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} -> {self.product.name}: {self.rating}*"




class Wishlist(models.Model):
    """Foydalanuvchining sevimli mahsulotlari"""
    user       = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="wishlist")
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ["user", "product"]
        verbose_name        = "Sevimlilar"
        verbose_name_plural = "Sevimlilar"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.product.name}"
