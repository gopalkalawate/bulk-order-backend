from rest_framework import status
from rest_framework.response import Response

from vendors.models import VendorServiceableLocation
from vendors.serializers import VendorServiceableLocationSerializer


class RemoveServiceableLocationHelper:
    def handle(self, request):
        serializer = VendorServiceableLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor = serializer.validated_data["vendor"]
        service_location = serializer.validated_data["service_location"]

        if vendor.home_service_location_id == service_location.id:
            return Response(
                {"error": "Vendor home service location cannot be removed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count, _ = VendorServiceableLocation.objects.filter(
            vendor=vendor,
            service_location=service_location,
        ).delete()

        if deleted_count == 0:
            return Response({"error": "Vendor serviceable location not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
