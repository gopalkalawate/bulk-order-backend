from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.response import Response

from config.cache_utils import bump_vendor_cache_version
from vendors.models import VendorServiceableLocation
from vendors.serializers import SetVendorLocationSerializer, VendorSerializer


class SetVendorLocationHelper:
    def handle(self, request):
        serializer = SetVendorLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor = serializer.validated_data["vendor"]
        service_location = serializer.validated_data["service_location"]
        latitude = serializer.validated_data.get("latitude")
        longitude = serializer.validated_data.get("longitude")

        vendor.home_service_location = service_location
        if latitude is not None and longitude is not None:
            vendor.location = Point(longitude, latitude, srid=4326)
        vendor.save()

        VendorServiceableLocation.objects.get_or_create(
            vendor=vendor,
            service_location=service_location,
        )

        bump_vendor_cache_version(vendor.id)

        return Response(VendorSerializer(vendor).data, status=status.HTTP_200_OK)
