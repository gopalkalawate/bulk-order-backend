from django.core.cache import cache
from django.contrib.gis.geos import Point
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from config.cache_utils import build_vendor_service_locations_cache_key
from location_module.models import ServiceLocation
from users.models import User
from .models import Vendor, VendorServiceableLocation


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "vendor-endpoint-tests",
        }
    }
)
class VendorEndpointTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="password",
            full_name="Admin User",
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.user)
        self.home_location = ServiceLocation.objects.create(
            name="Pune Central",
            point=Point(73.8567, 18.5204, srid=4326),
        )
        self.nearby_location = ServiceLocation.objects.create(
            name="Pune West",
            point=Point(73.8000, 18.5200, srid=4326),
        )
        self.far_location = ServiceLocation.objects.create(
            name="Mumbai",
            point=Point(72.8777, 19.0760, srid=4326),
        )

    def test_create_vendor_with_location(self):
        response = self.client.post(
            reverse("create_vendor"),
            {
                "name": "Fresh Supply Co",
                "email": "vendor@example.com",
                "phone": "9876543210",
                "latitude": 18.5204,
                "longitude": 73.8567,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vendor = Vendor.objects.get(id=response.data["id"])
        self.assertEqual(vendor.name, "Fresh Supply Co")
        self.assertIsNotNone(vendor.location)
        self.assertEqual(float(vendor.location.y), 18.5204)
        self.assertEqual(float(vendor.location.x), 73.8567)

    def test_set_vendor_location_creates_home_serviceable_mapping(self):
        vendor = Vendor.objects.create(name="Fresh Supply Co")

        response = self.client.post(
            reverse("set_vendor_location"),
            {
                "vendor_id": vendor.id,
                "service_location_id": self.home_location.id,
                "latitude": 18.5204,
                "longitude": 73.8567,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vendor.refresh_from_db()
        self.assertEqual(vendor.home_service_location_id, self.home_location.id)
        self.assertTrue(
            VendorServiceableLocation.objects.filter(
                vendor=vendor,
                service_location=self.home_location,
            ).exists()
        )

    def test_add_serviceable_location_is_idempotent(self):
        vendor = Vendor.objects.create(name="Fresh Supply Co")

        first_response = self.client.post(
            reverse("add_serviceable_location"),
            {"vendor_id": vendor.id, "service_location_id": self.nearby_location.id},
            format="json",
        )
        second_response = self.client.post(
            reverse("add_serviceable_location"),
            {"vendor_id": vendor.id, "service_location_id": self.nearby_location.id},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            VendorServiceableLocation.objects.filter(
                vendor=vendor,
                service_location=self.nearby_location,
            ).count(),
            1,
        )

    def test_remove_serviceable_location_rejects_home_location(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            home_service_location=self.home_location,
        )
        VendorServiceableLocation.objects.create(vendor=vendor, service_location=self.home_location)

        response = self.client.post(
            reverse("remove_serviceable_location"),
            {"vendor_id": vendor.id, "service_location_id": self.home_location.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            VendorServiceableLocation.objects.filter(
                vendor=vendor,
                service_location=self.home_location,
            ).exists()
        )

    def test_remove_serviceable_location_deletes_non_home_location(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            home_service_location=self.home_location,
        )
        VendorServiceableLocation.objects.create(vendor=vendor, service_location=self.nearby_location)

        response = self.client.post(
            reverse("remove_serviceable_location"),
            {"vendor_id": vendor.id, "service_location_id": self.nearby_location.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            VendorServiceableLocation.objects.filter(
                vendor=vendor,
                service_location=self.nearby_location,
            ).exists()
        )

    def test_get_service_locations_requires_vendor_location(self):
        vendor = Vendor.objects.create(name="Fresh Supply Co")

        response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Vendor location is not set")

    def test_get_service_locations_returns_locations_within_20km(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
            home_service_location=self.home_location,
        )
        VendorServiceableLocation.objects.create(vendor=vendor, service_location=self.home_location)

        response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        location_names = {location["name"] for location in response.data}
        self.assertIn(self.home_location.name, location_names)
        self.assertIn(self.nearby_location.name, location_names)
        self.assertNotIn(self.far_location.name, location_names)

        home_payload = next(location for location in response.data if location["id"] == self.home_location.id)
        self.assertTrue(home_payload["is_home_location"])
        self.assertTrue(home_payload["is_already_serviceable"])

    def test_get_service_locations_populates_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
        )

        response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cache_key = build_vendor_service_locations_cache_key(vendor.id)
        self.assertEqual(cache.get(cache_key), response.data)

    def test_get_service_locations_reads_cached_payload(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
        )

        first_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})
        ServiceLocation.objects.filter(id=self.nearby_location.id).update(name="Pune West Renamed")
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data, first_response.data)
        self.assertIn(self.nearby_location.name, {location["name"] for location in second_response.data})

    def test_add_serviceable_location_invalidates_vendor_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
        )
        self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        add_response = self.client.post(
            reverse("add_serviceable_location"),
            {"vendor_id": vendor.id, "service_location_id": self.nearby_location.id},
            format="json",
        )
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)
        nearby_payload = next(location for location in second_response.data if location["id"] == self.nearby_location.id)
        self.assertTrue(nearby_payload["is_already_serviceable"])

    def test_remove_serviceable_location_invalidates_vendor_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
            home_service_location=self.home_location,
        )
        VendorServiceableLocation.objects.create(vendor=vendor, service_location=self.nearby_location)
        self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        remove_response = self.client.post(
            reverse("remove_serviceable_location"),
            {"vendor_id": vendor.id, "service_location_id": self.nearby_location.id},
            format="json",
        )
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(remove_response.status_code, status.HTTP_204_NO_CONTENT)
        nearby_payload = next(location for location in second_response.data if location["id"] == self.nearby_location.id)
        self.assertFalse(nearby_payload["is_already_serviceable"])

    def test_set_vendor_location_invalidates_vendor_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(72.8777, 19.0760, srid=4326),
        )
        first_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        set_response = self.client.post(
            reverse("set_vendor_location"),
            {
                "vendor_id": vendor.id,
                "service_location_id": self.home_location.id,
                "latitude": 18.5204,
                "longitude": 73.8567,
            },
            format="json",
        )
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(set_response.status_code, status.HTTP_200_OK)
        self.assertIn(self.far_location.name, {location["name"] for location in first_response.data})
        self.assertIn(self.home_location.name, {location["name"] for location in second_response.data})

    def test_create_service_location_invalidates_vendor_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
        )
        first_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        ServiceLocation.objects.create(
            name="Pune East",
            point=Point(73.9000, 18.5200, srid=4326),
        )
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertNotIn("Pune East", {location["name"] for location in first_response.data})
        self.assertIn("Pune East", {location["name"] for location in second_response.data})

    def test_update_service_location_invalidates_vendor_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
        )
        inactive_location = ServiceLocation.objects.create(
            name="Pune North",
            point=Point(73.8567, 18.5600, srid=4326),
            is_active=False,
        )
        first_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        inactive_location.is_active = True
        inactive_location.save()
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertNotIn("Pune North", {location["name"] for location in first_response.data})
        self.assertIn("Pune North", {location["name"] for location in second_response.data})

    def test_delete_service_location_invalidates_vendor_cache(self):
        vendor = Vendor.objects.create(
            name="Fresh Supply Co",
            location=Point(73.8567, 18.5204, srid=4326),
        )
        first_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.nearby_location.delete()
        second_response = self.client.get(reverse("get_vendor_service_locations"), {"vendor_id": vendor.id})

        self.assertIn(self.nearby_location.name, {location["name"] for location in first_response.data})
        self.assertNotIn(self.nearby_location.name, {location["name"] for location in second_response.data})
