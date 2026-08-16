from django.contrib.gis.db import models

from location_module.models import ServiceLocation
from items.models import Item
from django.conf import settings


class Vendor(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="vendor_id")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    location = models.PointField(geography=True, srid=4326, blank=True, null=True)
    home_service_location = models.ForeignKey(
        ServiceLocation,
        on_delete=models.PROTECT,
        related_name="home_vendors",
        blank=True,
        null=True,
    )
    partner_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="vendor_profile",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vendors"
        ordering = ["name"]
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        return self.name


class VendorServiceableLocation(models.Model):
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="serviceable_locations",
    )
    service_location = models.ForeignKey(
        ServiceLocation,
        on_delete=models.CASCADE,
        related_name="serviceable_vendors",
    )

    class Meta:
        db_table = "vendor_serviceable_locations"
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "service_location"],
                name="unique_vendor_serviceable_location",
            )
        ]
        ordering = ["vendor", "service_location"]
        verbose_name = "Vendor Serviceable Location"
        verbose_name_plural = "Vendor Serviceable Locations"

    def __str__(self):
        return f"{self.vendor} -> {self.service_location}"


class VendorItem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="vendor_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="vendor_items")

    class Meta:
        db_table = "vendor_items"
        constraints = [
            models.UniqueConstraint(fields=["vendor", "item"], name="unique_vendor_item")
        ]

    def __str__(self):
        return f"{self.vendor} -> {self.item}"
