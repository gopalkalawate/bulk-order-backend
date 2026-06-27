from django.conf import settings
from django.contrib.gis.db import models


class ServiceLocation(models.Model):
    """
    Locations where the platform provides delivery service.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    point = models.PointField(
        geography=True,
        srid=4326,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "service_locations"
        ordering = ["name"]
        verbose_name = "Service Location"
        verbose_name_plural = "Service Locations"

    def __str__(self):
        return self.name


class UserServiceLocation(models.Model):
    """
    Relationship table between a user and a service location.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_location",
    )
    service_location = models.ForeignKey(
        ServiceLocation,
        on_delete=models.CASCADE,
        related_name="users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_service_locations"
        ordering = ["user", "service_location"]
        verbose_name = "User Service Location"
        verbose_name_plural = "User Service Locations"

    def __str__(self):
        return f"{self.user} -> {self.service_location}"
