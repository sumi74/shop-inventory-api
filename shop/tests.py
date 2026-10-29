from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from .models import Category, Product


class ShopAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="pass12345", is_staff=True)
        self.cashier = User.objects.create_user("cashier", password="pass12345")
        category = Category.objects.create(name="Drinks")
        self.product = Product.objects.create(
            name="Soda", category=category, price=4000, quantity_in_stock=10
        )

    def test_login_required(self):
        response = self.client.get("/api/products/")
        self.assertIn(response.status_code, (401, 403))

    def test_sale_reduces_stock(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.post(
            "/api/sales/",
            {"items": [{"product": self.product.id, "quantity": 2}]},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 8)

    def test_cannot_oversell(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.post(
            "/api/sales/",
            {"items": [{"product": self.product.id, "quantity": 50}]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 10)

    def test_cashier_cannot_add_product(self):
        self.client.force_authenticate(self.cashier)
        response = self.client.post(
            "/api/products/",
            {"name": "Water", "category": self.product.category.id,
             "price": "1000", "quantity_in_stock": 5},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_summary_is_owner_only(self):
        self.client.force_authenticate(self.cashier)
        self.assertEqual(self.client.get("/api/sales/summary/").status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get("/api/sales/summary/").status_code, 200)
