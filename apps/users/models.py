import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email majburiy")
        email = self.normalize_email(email).lower()
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser is_staff=True bo'lishi kerak")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser is_superuser=True bo'lishi kerak")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True)
    full_name   = models.CharField(max_length=255)
    phone       = models.CharField(max_length=20, blank=True, db_index=True)
    avatar      = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name"]
    objects = UserManager()

    class Meta:
        verbose_name        = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Address(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title      = models.CharField(max_length=100)
    city       = models.CharField(max_length=100)
    district   = models.CharField(max_length=100)
    street     = models.CharField(max_length=255)
    extra_info = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name        = "Manzil"
        verbose_name_plural = "Manzillar"

    def __str__(self):
        return f"{self.user.full_name} — {self.title}"

    def save(self, *args, **kwargs):
        # Faqat bitta default manzil bo'lishi uchun
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
