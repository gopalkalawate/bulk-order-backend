from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework import status
from rest_framework.response import Response

from location_module.models import ServiceLocation
from vendors.models import Vendor
from vendors.serializers import NearbyVendorServiceLocationSerializer


class GetVendorServiceLocationsHelper:
    def handle(self, request):
        vendor_id = request.query_params.get("vendor_id")
        if not vendor_id:
            return Response({"error": "vendor_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(id=vendor_id, is_active=True)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

        if not vendor.location:
            return Response({"error": "Vendor location is not set"}, status=status.HTTP_400_BAD_REQUEST)

        serviceable_location_ids = set(
            vendor.serviceable_locations.values_list("service_location_id", flat=True)
        )
        nearby_locations = (
            ServiceLocation.objects.filter(is_active=True, point__distance_lte=(vendor.location, D(km=20)))
            .annotate(distance=Distance("point", vendor.location))
            .order_by("distance", "name")
        )

        serializer = NearbyVendorServiceLocationSerializer(
            nearby_locations,
            many=True,
            context={
                "vendor": vendor,
                "serviceable_location_ids": serviceable_location_ids,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
