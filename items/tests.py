from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from users.models import User
from .models import Item, ItemCategory


class ItemEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="password",
            full_name="Admin User",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.user)
        self.category = ItemCategory.objects.create(name="Vegetables")

    def test_create_category(self):
        response = self.client.post(
            reverse("create_item_category"),
            {"name": "Grains"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Grains")
        self.assertTrue(ItemCategory.objects.filter(name="Grains").exists())

    def test_create_category_rejects_duplicate_name(self):
        response = self.client.post(
            reverse("create_item_category"),
            {"name": self.category.name},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_item_with_required_quantity(self):
        response = self.client.post(
            reverse("create_item"),
            {
                "name": "Tomato",
                "description": "Fresh red tomato",
                "category_id": self.category.id,
                "quantity": "5.50",
                "unit": "kg",
                "image_url": "https://example.com/tomato.jpg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Tomato")
        self.assertEqual(response.data["quantity"], "5.50")
        self.assertEqual(response.data["unit"], "kg")
        self.assertEqual(response.data["image_url"], "https://example.com/tomato.jpg")
        self.assertEqual(response.data["category"]["category_id"], self.category.id)

    def test_create_item_requires_quantity(self):
        response = self.client.post(
            reverse("create_item"),
            {"name": "Tomato"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_create_item_rejects_invalid_quantities(self):
        for quantity in ["0", "-1"]:
            with self.subTest(quantity=quantity):
                response = self.client.post(
                    reverse("create_item"),
                    {"name": "Tomato", "quantity": quantity},
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("quantity", response.data)

    def test_create_item_rejects_invalid_category(self):
        response = self.client.post(
            reverse("create_item"),
            {"name": "Tomato", "quantity": "1.00", "category_id": 999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id", response.data)

    def test_search_items_matches_full_text(self):
        Item.objects.create(
            name="Basmati Rice",
            description="Long grain premium rice",
            category=self.category,
            quantity="10.00",
            unit="kg",
        )

        response = self.client.get(reverse("search_items"), {"q": "premium rice"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Basmati Rice")

    def test_search_items_matches_fuzzy_typo(self):
        Item.objects.create(
            name="Tomato",
            description="Fresh red tomato",
            category=self.category,
            quantity="5.00",
            unit="kg",
        )

        response = self.client.get(reverse("search_items"), {"q": "tomto"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Tomato")

    def test_search_items_filters_category_and_active_state(self):
        grains = ItemCategory.objects.create(name="Grains")
        Item.objects.create(name="Active Rice", category=grains, quantity="1.00", unit="kg", is_active=True)
        Item.objects.create(name="Inactive Rice", category=grains, quantity="1.00", unit="kg", is_active=False)
        Item.objects.create(name="Vegetable Rice Mix", category=self.category, quantity="1.00", unit="kg", is_active=True)

        response = self.client.get(
            reverse("search_items"),
            {"q": "rice", "category_id": grains.id, "is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["name"] for item in response.data], ["Active Rice"])

    def test_search_items_caps_limit(self):
        for index in range(55):
            Item.objects.create(name=f"Rice {index}", quantity="1.00", unit="kg")

        response = self.client.get(reverse("search_items"), {"q": "rice", "limit": "100"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 50)

    def test_search_items_requires_q(self):
        response = self.client.get(reverse("search_items"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "q is required")

    def test_update_item_partial_payload(self):
        item = Item.objects.create(
            name="Tomato",
            category=self.category,
            quantity="5.00",
            unit="kg",
            image_url="https://example.com/old.jpg",
        )

        response = self.client.patch(
            reverse("update_item", kwargs={"item_id": item.id}),
            {"quantity": "7.25", "image_url": "https://example.com/new.jpg"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(str(item.quantity), "7.25")
        self.assertEqual(item.name, "Tomato")
        self.assertEqual(item.image_url, "https://example.com/new.jpg")

    def test_update_item_rejects_invalid_quantity(self):
        item = Item.objects.create(name="Tomato", quantity="5.00")

        response = self.client.patch(
            reverse("update_item", kwargs={"item_id": item.id}),
            {"quantity": "0"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_search_vector_refreshes_after_update(self):
        item = Item.objects.create(name="Tomato", description="Fresh produce", quantity="5.00")

        update_response = self.client.patch(
            reverse("update_item", kwargs={"item_id": item.id}),
            {"name": "Potato", "description": "Starchy vegetable"},
            format="json",
        )
        search_response = self.client.get(reverse("search_items"), {"q": "potato"})

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(search_response.data[0]["item_id"], item.id)
