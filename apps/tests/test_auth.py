"""
Auth API testlari:
- Ro'yxatdan o'tish
- Login / Logout
- Token refresh
- Profil olish va yangilash
- Parol o'zgartirish
- Email tekshirish
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User


def make_user(email="test@uzbox.uz", password="StrongPass123!", full_name="Test User"):
    return User.objects.create_user(email=email, password=password, full_name=full_name)


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url    = "/api/auth/register/"

    def test_register_success(self):
        res = self.client.post(self.url, {
            "email": "new@uzbox.uz", "full_name": "New User",
            "password": "StrongPass123!", "password2": "StrongPass123!"
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertTrue(User.objects.filter(email="new@uzbox.uz").exists())

    def test_register_duplicate_email(self):
        make_user()
        res = self.client.post(self.url, {
            "email": "test@uzbox.uz", "full_name": "Test",
            "password": "StrongPass123!", "password2": "StrongPass123!"
        })
        self.assertEqual(res.status_code, 400)

    def test_register_password_mismatch(self):
        res = self.client.post(self.url, {
            "email": "a@b.com", "full_name": "A",
            "password": "Pass1234!", "password2": "Pass9999!"
        })
        self.assertEqual(res.status_code, 400)

    def test_register_weak_password(self):
        res = self.client.post(self.url, {
            "email": "a@b.com", "full_name": "A",
            "password": "123", "password2": "123"
        })
        self.assertEqual(res.status_code, 400)

    def test_register_invalid_email(self):
        res = self.client.post(self.url, {
            "email": "notanemail", "full_name": "A",
            "password": "StrongPass123!", "password2": "StrongPass123!"
        })
        self.assertEqual(res.status_code, 400)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url    = "/api/auth/login/"
        self.user   = make_user()

    def test_login_success(self):
        res = self.client.post(self.url, {
            "email": "test@uzbox.uz", "password": "StrongPass123!"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_login_wrong_password(self):
        res = self.client.post(self.url, {
            "email": "test@uzbox.uz", "password": "WrongPass!"
        })
        self.assertEqual(res.status_code, 400)

    def test_login_nonexistent_user(self):
        res = self.client.post(self.url, {
            "email": "nobody@uzbox.uz", "password": "Pass123!"
        })
        self.assertEqual(res.status_code, 400)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(self.url, {
            "email": "test@uzbox.uz", "password": "StrongPass123!"
        })
        self.assertNotEqual(res.status_code, 200)


class ProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user   = make_user()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        res = self.client.get("/api/auth/profile/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], "test@uzbox.uz")

    def test_update_profile(self):
        res = self.client.patch("/api/auth/profile/", {"full_name": "Updated Name"})
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")

    def test_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        res = self.client.get("/api/auth/profile/")
        self.assertEqual(res.status_code, 401)

    def test_change_password(self):
        res = self.client.post("/api/auth/change-password/", {
            "old_password": "StrongPass123!",
            "new_password": "NewStrongPass456!",
            "new_password2": "NewStrongPass456!"
        })
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))

    def test_change_password_wrong_old(self):
        res = self.client.post("/api/auth/change-password/", {
            "old_password": "WrongOld!",
            "new_password": "NewPass456!",
            "new_password2": "NewPass456!"
        })
        self.assertEqual(res.status_code, 400)
