"""
Products API testlari:
- Kategoriyalar
- Mahsulotlar ro'yxati, filter, search
- Mahsulot detail
- Review qo'shish
- Wishlist
"""
from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.products.models import Category, Product, Review, Wishlist


def make_category(name="Elektronika"):
    return Category.objects.create(name=name, slug=name.lower())


def make_product(category, name="iPhone 15", price=10_000_000, stock=10):
    return Product.objects.create(
        name=name, slug=name.lower().replace(" ", "-"),
        description="Test mahsulot", category=category,
        price=price, stock=stock, is_active=True
    )


def make_user(email="u@test.uz"):
    return User.objects.create_user(email=email, password="Pass123!", full_name="Test")


class CategoryTests(TestCase):
    def setUp(self):
        self.client   = APIClient()
        self.category = make_category()

    def test_list_categories(self):
        res = self.client.get("/api/products/categories/")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data), 1)

    def test_inactive_category_hidden(self):
        Category.objects.create(name="Yashirin", slug="yashirin", is_active=False)
        res = self.client.get("/api/products/categories/")
        # Paginated yoki oddiy list bo'lishi mumkin
        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        names = [c["name"] for c in data]
        self.assertNotIn("Yashirin", names)


class ProductTests(TestCase):
    def setUp(self):
        self.client   = APIClient()
        self.category = make_category()
        self.product  = make_product(self.category)

    def test_list_products(self):
        res = self.client.get("/api/products/")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.data["count"], 1)

    def test_product_detail(self):
        res = self.client.get(f"/api/products/{self.product.slug}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name"], self.product.name)

    def test_product_detail_404(self):
        res = self.client.get("/api/products/notexist-slug/")
        self.assertEqual(res.status_code, 404)

    def test_filter_by_category(self):
        res = self.client.get(f"/api/products/?category={self.category.slug}")
        self.assertEqual(res.status_code, 200)
        for p in res.data["results"]:
            self.assertEqual(p["category_name"], self.category.name)

    def test_filter_has_discount(self):
        self.product.discount_price = 8_000_000
        self.product.save()
        res = self.client.get("/api/products/?has_discount=true")
        self.assertEqual(res.status_code, 200)
        ids = [p["id"] for p in res.data["results"]]
        self.assertIn(str(self.product.id), ids)

    def test_search(self):
        res = self.client.get("/api/products/?search=iPhone")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.data["count"], 1)

    def test_autocomplete(self):
        res = self.client.get("/api/products/autocomplete/?q=iPh")
        self.assertEqual(res.status_code, 200)

    def test_autocomplete_short_query(self):
        res = self.client.get("/api/products/autocomplete/?q=i")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0)

    def test_inactive_product_hidden(self):
        p = make_product(self.category, name="Yashirin", stock=5)
        p.is_active = False
        p.save()
        res = self.client.get(f"/api/products/{p.slug}/")
        self.assertEqual(res.status_code, 404)

    def test_current_price_with_discount(self):
        self.product.discount_price = 8_000_000
        self.product.save()
        self.assertEqual(float(self.product.current_price), 8_000_000)

    def test_current_price_without_discount(self):
        self.assertEqual(float(self.product.current_price), 10_000_000)


class ReviewTests(TestCase):
    def setUp(self):
        self.client  = APIClient()
        self.category = make_category()
        self.product  = make_product(self.category)
        self.user     = make_user()
        self.client.force_authenticate(user=self.user)

    def test_add_review(self):
        res = self.client.post(
            f"/api/products/{self.product.slug}/reviews/",
            {"rating": 5, "comment": "Ajoyib mahsulot!"}
        )
        self.assertEqual(res.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_count, 1)
        self.assertEqual(float(self.product.rating_avg), 5.0)

    def test_duplicate_review_fails(self):
        self.client.post(
            f"/api/products/{self.product.slug}/reviews/",
            {"rating": 4, "comment": "Yaxshi"}
        )
        res = self.client.post(
            f"/api/products/{self.product.slug}/reviews/",
            {"rating": 3, "comment": "Yana"}
        )
        self.assertEqual(res.status_code, 400)

    def test_review_invalid_rating(self):
        res = self.client.post(
            f"/api/products/{self.product.slug}/reviews/",
            {"rating": 6, "comment": "Test"}
        )
        self.assertEqual(res.status_code, 400)

    def test_review_unauthenticated(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(
            f"/api/products/{self.product.slug}/reviews/",
            {"rating": 5, "comment": "Test"}
        )
        self.assertEqual(res.status_code, 401)


class WishlistTests(TestCase):
    def setUp(self):
        self.client  = APIClient()
        self.category = make_category()
        self.product  = make_product(self.category)
        self.user     = make_user()
        self.client.force_authenticate(user=self.user)

    def test_add_to_wishlist(self):
        res = self.client.post(f"/api/auth/wishlist/{self.product.id}/toggle/")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["action"], "added")

    def test_remove_from_wishlist(self):
        self.client.post(f"/api/auth/wishlist/{self.product.id}/toggle/")
        res = self.client.post(f"/api/auth/wishlist/{self.product.id}/toggle/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["action"], "removed")

    def test_wishlist_list(self):
        self.client.post(f"/api/auth/wishlist/{self.product.id}/toggle/")
        res = self.client.get("/api/auth/wishlist/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_wishlist_clear(self):
        self.client.post(f"/api/auth/wishlist/{self.product.id}/toggle/")
        res = self.client.delete("/api/auth/wishlist/clear/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Wishlist.objects.filter(user=self.user).count(), 0)

    def test_wishlist_unauthenticated(self):
        self.client.force_authenticate(user=None)
        res = self.client.get("/api/auth/wishlist/")
        self.assertEqual(res.status_code, 401)