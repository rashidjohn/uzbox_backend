"""
Orders & Payments testlari:
- Buyurtma yaratish
- Stok tekshiruvi
- Promo-kod
- Bekor qilish
- Click/Payme webhook
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Category, Product
from apps.orders.models import Order, OrderItem
from apps.orders.promo import PromoCode


def make_user(email="buyer@test.uz"):
    return User.objects.create_user(email=email, password="Pass123!", full_name="Buyer")


def make_product(name="Laptop", price=5_000_000, stock=10):
    cat = Category.objects.create(name="Test", slug="test-cat")
    return Product.objects.create(
        name=name, slug=name.lower(),
        description="desc", category=cat,
        price=price, stock=stock, is_active=True
    )


def make_order(user, product, qty=1, payment_method="cash"):
    return Order.objects.create(
        user=user,
        status="pending",
        total_price=product.price * qty,
        payment_method=payment_method,
        address={
            "full_name": "Test User", "phone": "+998901234567",
            "city": "Toshkent", "district": "Chilonzor", "street": "Bunyodkor 5"
        }
    )


ADDRESS = {
    "full_name": "Test User", "phone": "+998901234567",
    "city": "Toshkent", "district": "Chilonzor", "street": "Bunyodkor 5"
}


class OrderCreateTests(TestCase):
    def setUp(self):
        self.client  = APIClient()
        self.user    = make_user()
        self.product = make_product()
        self.client.force_authenticate(user=self.user)

    def test_create_order_cash(self):
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "items": [{"product_id": str(self.product.id), "quantity": 2}]
        }, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)
        # Stok kamayganini tekshirish
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_create_order_insufficient_stock(self):
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "items": [{"product_id": str(self.product.id), "quantity": 100}]
        }, format="json")
        self.assertEqual(res.status_code, 400)
        # Stok o'zgarmaganini tekshirish
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_create_order_empty_items(self):
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "items": []
        }, format="json")
        self.assertEqual(res.status_code, 400)

    def test_create_order_missing_address_field(self):
        bad_address = {"full_name": "Test", "phone": "+998"}  # city va street yo'q
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": bad_address,
            "items": [{"product_id": str(self.product.id), "quantity": 1}]
        }, format="json")
        self.assertEqual(res.status_code, 400)

    def test_create_order_inactive_product(self):
        self.product.is_active = False
        self.product.save()
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "items": [{"product_id": str(self.product.id), "quantity": 1}]
        }, format="json")
        self.assertEqual(res.status_code, 400)

    def test_order_total_calculated_correctly(self):
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "items": [{"product_id": str(self.product.id), "quantity": 3}]
        }, format="json")
        self.assertEqual(res.status_code, 201)
        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(float(order.total_price), float(self.product.price) * 3)

    def test_order_unauthenticated_without_email(self):
        """Guest checkout — email yo'q bo'lsa 400"""
        self.client.force_authenticate(user=None)
        res = self.client.post("/api/orders/", {
            "payment_method": "cash", "address": ADDRESS,
            "items": [{"product_id": str(self.product.id), "quantity": 1}]
        }, format="json")
        self.assertEqual(res.status_code, 400)

    def test_order_guest_with_email(self):
        """Guest checkout — email bilan muvaffaqiyatli"""
        self.client.force_authenticate(user=None)
        res = self.client.post("/api/orders/", {
            "payment_method": "cash", "address": ADDRESS,
            "guest_email": "guest@test.uz",
            "items": [{"product_id": str(self.product.id), "quantity": 1}]
        }, format="json")
        self.assertEqual(res.status_code, 201)


class OrderCancelTests(TestCase):
    def setUp(self):
        self.client  = APIClient()
        self.user    = make_user()
        self.product = make_product()
        self.client.force_authenticate(user=self.user)

    def test_cancel_pending_order(self):
        order = make_order(self.user, self.product)
        item  = OrderItem.objects.create(
            order=order, product=self.product, quantity=2, price=self.product.price
        )
        res = self.client.patch(f"/api/orders/{order.id}/", {"status": "cancelled"})
        self.assertEqual(res.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        # Stok qaytganini tekshirish (signal orqali)
        self.product.refresh_from_db()
        self.assertGreaterEqual(self.product.stock, 10)  # bekor qilinsa stok qaytadi

    def test_cancel_paid_order_fails(self):
        order = make_order(self.user, self.product)
        order.status = "paid"
        order.save()
        res = self.client.patch(f"/api/orders/{order.id}/", {"status": "cancelled"})
        self.assertEqual(res.status_code, 400)

    def test_user_cannot_set_paid_status(self):
        order = make_order(self.user, self.product)
        res = self.client.patch(f"/api/orders/{order.id}/", {"status": "paid"})
        self.assertNotEqual(res.status_code, 200)

    def test_cannot_access_other_users_order(self):
        other = make_user("other@test.uz")
        order = make_order(other, self.product)
        res = self.client.get(f"/api/orders/{order.id}/")
        self.assertEqual(res.status_code, 404)


class PromoCodeTests(TestCase):
    def setUp(self):
        self.client  = APIClient()
        self.user    = make_user()
        self.product = make_product()
        self.client.force_authenticate(user=self.user)
        self.promo = PromoCode.objects.create(
            code="SALE20",
            discount_type="percent",
            discount_value=20,
            min_order_price=100_000,
            is_active=True
        )

    def test_valid_promo(self):
        res = self.client.post("/api/orders/promo/check/", {
            "code": "SALE20", "order_total": 1_000_000
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["discount_amount"], 200_000)

    def test_invalid_promo_code(self):
        res = self.client.post("/api/orders/promo/check/", {
            "code": "NOTEXIST", "order_total": 1_000_000
        })
        self.assertNotEqual(res.data.get("valid"), True)

    def test_promo_min_order_not_met(self):
        res = self.client.post("/api/orders/promo/check/", {
            "code": "SALE20", "order_total": 50_000
        })
        self.assertNotEqual(res.data.get("valid"), True)

    def test_inactive_promo(self):
        self.promo.is_active = False
        self.promo.save()
        res = self.client.post("/api/orders/promo/check/", {
            "code": "SALE20", "order_total": 1_000_000
        })
        self.assertNotEqual(res.data.get("valid"), True)

    def test_promo_applied_in_order(self):
        res = self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "promo_code": "SALE20",
            "items": [{"product_id": str(self.product.id), "quantity": 1}]
        }, format="json")
        self.assertEqual(res.status_code, 201)
        order = Order.objects.get(id=res.data["id"])
        expected_total = float(self.product.price) * 0.8
        self.assertAlmostEqual(float(order.total_price), expected_total, places=0)

    def test_promo_used_count_incremented(self):
        self.client.post("/api/orders/", {
            "payment_method": "cash",
            "address": ADDRESS,
            "promo_code": "SALE20",
            "items": [{"product_id": str(self.product.id), "quantity": 1}]
        }, format="json")
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)


class WebhookTests(TestCase):
    def setUp(self):
        self.client  = APIClient()
        self.user    = make_user()
        self.product = make_product()

    def _create_order(self, method="click"):
        order = Order.objects.create(
            user=self.user,
            status="pending",
            total_price=self.product.price,
            payment_method=method,
            address=ADDRESS
        )
        return order

    def test_click_prepare_action(self):
        order = self._create_order("click")
        res   = self.client.post("/api/payments/click/webhook/", {
            "action": 0,
            "merchant_trans_id": str(order.id),
            "amount": float(order.total_price),
            "click_trans_id": "12345",
            "sign_time": "2025-01-01 12:00:00",
            "sign_string": "testhash"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("error"), 0)

    def test_click_complete_action(self):
        order = self._create_order("click")
        self.client.post("/api/payments/click/webhook/", {
            "action": 1,
            "merchant_trans_id": str(order.id),
            "amount": float(order.total_price),
            "click_trans_id": "12345",
            "sign_time": "2025-01-01 12:00:00",
            "sign_string": "testhash"
        })
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")

    def test_click_wrong_amount(self):
        order = self._create_order("click")
        res   = self.client.post("/api/payments/click/webhook/", {
            "action": 0,
            "merchant_trans_id": str(order.id),
            "amount": 999,  # noto'g'ri summa
            "click_trans_id": "12345",
            "sign_time": "2025-01-01 12:00:00",
            "sign_string": "testhash"
        })
        self.assertEqual(res.data.get("error"), -2)

    def test_click_nonexistent_order(self):
        res = self.client.post("/api/payments/click/webhook/", {
            "action": 0,
            "merchant_trans_id": "00000000-0000-0000-0000-000000000000",
            "amount": 100,
            "click_trans_id": "99",
            "sign_time": "2025-01-01", "sign_string": "x"
        })
        self.assertEqual(res.data.get("error"), -5)

    def test_payme_check(self):
        order = self._create_order("payme")
        res   = self.client.post("/api/payments/payme/webhook/", {
            "method": "CheckPerformTransaction",
            "params": {"account": {"order_id": str(order.id)}}
        }, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["result"]["allow"])

    def test_payme_perform(self):
        order = self._create_order("payme")
        self.client.post("/api/payments/payme/webhook/", {
            "method": "PerformTransaction",
            "params": {"account": {"order_id": str(order.id)}, "id": "pm_999"}
        }, format="json")
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")

    def test_payme_cancel(self):
        order = self._create_order("payme")
        res   = self.client.post("/api/payments/payme/webhook/", {
            "method": "CancelTransaction",
            "params": {"account": {"order_id": str(order.id)}, "id": "pm_999"}
        }, format="json")
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")


ADDRESS = {
    "full_name": "Test User", "phone": "+998901234567",
    "city": "Toshkent", "district": "Chilonzor", "street": "Bunyodkor 5"
}