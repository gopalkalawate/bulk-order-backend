from django.contrib.gis.geos import Point
from rest_framework import serializers

from location_module.models import ServiceLocation
from users.models import User
from items.models import Item
from .models import Vendor, VendorServiceableLocation, VendorItem


class VendorSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    location_latitude = serializers.SerializerMethodField()
    location_longitude = serializers.SerializerMethodField()
    home_service_location_id = serializers.IntegerField(source="home_service_location.id", read_only=True)
    home_service_location_name = serializers.CharField(source="home_service_location.name", read_only=True)
    partner_user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "latitude",
            "longitude",
            "location_latitude",
            "location_longitude",
            "home_service_location_id",
            "home_service_location_name",
            "partner_user_id",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "location_latitude",
            "location_longitude",
            "home_service_location_id",
            "home_service_location_name",
            "is_active",
            "created_at",
        ]

    def validate(self, attrs):
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("latitude and longitude must be provided together")
        return attrs

    def create(self, validated_data):
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)
        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)

    def get_location_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_location_longitude(self, obj):
        return obj.location.x if obj.location else None


class LinkVendorPartnerSerializer(serializers.Serializer):
    partner_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.PARTNER), source="partner_user"
    )


class VendorItemSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.filter(is_active=True), source="item")

    class Meta:
        model = VendorItem
        fields = ["id", "item_id"]
        read_only_fields = ["id"]


class SetVendorLocationSerializer(serializers.Serializer):
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.filter(is_active=True),
        source="vendor",
    )
    service_location_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceLocation.objects.filter(is_active=True),
        source="service_location",
    )
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    def validate(self, attrs):
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("latitude and longitude must be provided together")
        return attrs


class VendorServiceableLocationSerializer(serializers.ModelSerializer):
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.filter(is_active=True),
        source="vendor",
        write_only=True,
    )
    service_location_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceLocation.objects.filter(is_active=True),
        source="service_location",
        write_only=True,
    )
    vendor = VendorSerializer(read_only=True)
    service_location = serializers.SerializerMethodField()

    class Meta:
        model = VendorServiceableLocation
        fields = ["id", "vendor_id", "service_location_id", "vendor", "service_location"]
        read_only_fields = ["id", "vendor", "service_location"]
        validators = []

    def get_service_location(self, obj):
        return {
            "id": obj.service_location.id,
            "name": obj.service_location.name,
            "is_active": obj.service_location.is_active,
        }


class NearbyVendorServiceLocationSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    is_home_location = serializers.SerializerMethodField()
    is_already_serviceable = serializers.SerializerMethodField()

    class Meta:
        model = ServiceLocation
        fields = ["id", "name", "distance_km", "is_active", "is_home_location", "is_already_serviceable"]

    def get_distance_km(self, obj):
        distance = getattr(obj, "distance", None)
        if distance is None:
            return None
        if hasattr(distance, "km"):
            return round(distance.km, 2)
        return round(float(distance) / 1000, 2)

    def get_is_home_location(self, obj):
        vendor = self.context.get("vendor")
        return bool(vendor and vendor.home_service_location_id == obj.id)

    def get_is_already_serviceable(self, obj):
        serviceable_location_ids = self.context.get("serviceable_location_ids", set())
        return obj.id in serviceable_location_ids
