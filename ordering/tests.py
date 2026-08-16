from datetime import timedelta
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from items.models import Item
from location_module.models import ServiceLocation, UserServiceLocation
from users.models import User
from vendors.models import Vendor, VendorItem, VendorServiceableLocation
from .models import OrderCycle, PurchaseOrder, UserOrder, VendorQuote


class OrderingFlowTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", full_name="Admin", role=User.Role.ADMIN)
        self.customer = User.objects.create_user(email="customer@example.com", password="pass", full_name="Customer")
        self.partner = User.objects.create_user(email="partner@example.com", password="pass", full_name="Partner", role=User.Role.PARTNER)
        self.location = ServiceLocation.objects.create(name="Central", point=Point(73.8, 18.5, srid=4326))
        UserServiceLocation.objects.create(user=self.customer, service_location=self.location)
        self.item = Item.objects.create(name="Rice", quantity="1.00", unit="kg")
        self.vendor = Vendor.objects.create(name="Supplier", partner_user=self.partner)
        VendorServiceableLocation.objects.create(vendor=self.vendor, service_location=self.location)
        VendorItem.objects.create(vendor=self.vendor, item=self.item)

    def cycle(self):
        now = timezone.now()
        return OrderCycle.objects.create(service_location=self.location, cycle_date=now.date(), order_window_start=now - timedelta(hours=1), order_window_end=now + timedelta(hours=1), quote_window_end=now + timedelta(hours=2))

    def test_customer_checkout_then_close_creates_quote_invitation(self):
        cycle = self.cycle()
        self.client.force_authenticate(self.customer)
        response = self.client.post(reverse("add_cart_item", args=[cycle.id]), {"item_id": self.item.id, "quantity": "2.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse("checkout", args=[cycle.id]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("close_order_cycle", args=[cycle.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(VendorQuote.objects.filter(cycle=cycle, vendor=self.vendor).exists())

    def test_customer_can_checkout_multiple_orders_in_the_same_cycle(self):
        cycle = self.cycle()
        self.client.force_authenticate(self.customer)

        self.client.post(reverse("add_cart_item", args=[cycle.id]), {"item_id": self.item.id, "quantity": "2.00"}, format="json")
        first_checkout = self.client.post(reverse("checkout", args=[cycle.id]))

        self.client.post(reverse("add_cart_item", args=[cycle.id]), {"item_id": self.item.id, "quantity": "3.00"}, format="json")
        second_checkout = self.client.post(reverse("checkout", args=[cycle.id]))

        self.assertEqual(first_checkout.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_checkout.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first_checkout.data["id"], second_checkout.data["id"])
        self.assertEqual(UserOrder.objects.filter(cycle=cycle, user=self.customer).count(), 2)

        response = self.client.get(reverse("orders"), {"cycle_id": cycle.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_lowest_eligible_quote_creates_purchase_order(self):
        cycle = self.cycle()
        self.client.force_authenticate(self.customer)
        self.client.post(reverse("add_cart_item", args=[cycle.id]), {"item_id": self.item.id, "quantity": "2.00"}, format="json")
        self.client.post(reverse("checkout", args=[cycle.id]))
        self.client.force_authenticate(self.admin)
        self.client.post(reverse("close_order_cycle", args=[cycle.id]))
        quote = VendorQuote.objects.get(cycle=cycle, vendor=self.vendor)
        self.client.force_authenticate(self.partner)
        self.client.put(reverse("set_quote_items", args=[quote.id]), [{"item_id": self.item.id, "unit_price": "10.00"}], format="json")
        self.client.post(reverse("submit_quote", args=[quote.id]))
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("select_cycle_quotes", args=[cycle.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        po = PurchaseOrder.objects.get(cycle=cycle, vendor=self.vendor)
        self.assertEqual(po.total_amount, Decimal("20.00"))
