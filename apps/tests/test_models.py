"""
Model testlari:
- Product current_price, discount_percent
- Order stock restore on cancel
- PromoCode is_valid, calculate_discount
- Unique slug
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.products.models import Category, Product
from apps.orders.models import Order, OrderItem
from apps.orders.promo import PromoCode


def make_cat():
    return Category.objects.create(name="Cat", slug="cat")


def make_user():
    return User.objects.create_user(
        email="m@test.uz", password="Pass123!", full_name="Model Test"
    )


class ProductModelTests(TestCase):
    def setUp(self):
        self.cat = make_cat()

    def test_current_price_no_discount(self):
        p = Product.objects.create(
            name="A", slug="a", description="x", category=self.cat,
            price=1_000_000, stock=5
        )
        self.assertEqual(p.current_price, Decimal("1000000"))

    def test_current_price_with_discount(self):
        p = Product.objects.create(
            name="B", slug="b", description="x", category=self.cat,
            price=1_000_000, discount_price=800_000, stock=5
        )
        self.assertEqual(p.current_price, Decimal("800000"))

    def test_discount_percent_auto_calculated(self):
        p = Product.objects.create(
            name="C", slug="c", description="x", category=self.cat,
            price=1_000_000, discount_price=750_000, stock=5
        )
        self.assertEqual(p.discount_percent, 25)

    def test_discount_price_gt_price_removed(self):
        p = Product.objects.create(
            name="D", slug="d", description="x", category=self.cat,
            price=1_000_000, discount_price=1_500_000, stock=5
        )
        self.assertIsNone(p.discount_price)

    def test_unique_slug_auto_incremented(self):
        p1 = Product.objects.create(
            name="Laptop", slug="laptop", description="x", category=self.cat,
            price=5_000_000, stock=1
        )
        p2 = Product(name="Laptop", description="x", category=self.cat, price=4_000_000, stock=1)
        p2.save()
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertTrue(p2.slug.startswith("laptop"))


class StockRestoreTests(TestCase):
    def setUp(self):
        self.user    = make_user()
        self.cat     = make_cat()
        self.product = Product.objects.create(
            name="P", slug="p", description="x", category=self.cat,
            price=100_000, stock=10
        )

    def test_stock_restored_on_cancel(self):
        order = Order.objects.create(
            user=self.user, status="pending",
            total_price=200_000, payment_method="cash",
            address={"full_name": "T", "phone": "x", "city": "T",
                     "district": "T", "street": "T"}
        )
        OrderItem.objects.create(
            order=order, product=self.product, quantity=3, price=100_000
        )
        # Stokni qo'lda kamaytirish (buyurtma create'da bo'lgan kabi)
        self.product.stock -= 3
        self.product.save()
        self.assertEqual(self.product.stock, 7)

        # Bekor qilish
        order.status = "cancelled"
        order.save()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_stock_not_restored_twice(self):
        order = Order.objects.create(
            user=self.user, status="cancelled",
            total_price=100_000, payment_method="cash",
            address={"full_name": "T", "phone": "x", "city": "T",
                     "district": "T", "street": "T"}
        )
        OrderItem.objects.create(
            order=order, product=self.product, quantity=2, price=100_000
        )
        stock_before = self.product.stock
        # Yana cancelled — signal ishlamasligi kerak (allaqachon cancelled)
        order.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before)


class PromoCodeModelTests(TestCase):
    def test_percent_discount(self):
        promo = PromoCode.objects.create(
            code="P20", discount_type="percent",
            discount_value=20, min_order_price=0, is_active=True
        )
        valid, _ = promo.is_valid(500_000)
        self.assertTrue(valid)
        self.assertEqual(promo.calculate_discount(500_000), 100_000)

    def test_fixed_discount(self):
        promo = PromoCode.objects.create(
            code="F50K", discount_type="fixed",
            discount_value=50_000, min_order_price=0, is_active=True
        )
        valid, _ = promo.is_valid(200_000)
        self.assertTrue(valid)
        self.assertEqual(promo.calculate_discount(200_000), 50_000)

    def test_fixed_discount_not_exceed_total(self):
        promo = PromoCode.objects.create(
            code="BIG", discount_type="fixed",
            discount_value=500_000, min_order_price=0, is_active=True
        )
        discount = promo.calculate_discount(100_000)
        self.assertLessEqual(discount, 100_000)

    def test_min_order_not_met(self):
        promo = PromoCode.objects.create(
            code="MIN", discount_type="percent",
            discount_value=10, min_order_price=1_000_000, is_active=True
        )
        valid, msg = promo.is_valid(500_000)
        self.assertFalse(valid)

    def test_expired_promo(self):
        promo = PromoCode.objects.create(
            code="EXP", discount_type="percent",
            discount_value=10, min_order_price=0, is_active=True,
            valid_until=timezone.now() - timedelta(days=1)
        )
        valid, _ = promo.is_valid(100_000)
        self.assertFalse(valid)

    def test_max_uses_reached(self):
        promo = PromoCode.objects.create(
            code="MAX", discount_type="percent",
            discount_value=10, min_order_price=0,
            is_active=True, max_uses=5, used_count=5
        )
        valid, _ = promo.is_valid(100_000)
        self.assertFalse(valid)

    def test_inactive_promo(self):
        promo = PromoCode.objects.create(
            code="OFF", discount_type="percent",
            discount_value=10, min_order_price=0, is_active=False
        )
        valid, _ = promo.is_valid(100_000)
        self.assertFalse(valid)
