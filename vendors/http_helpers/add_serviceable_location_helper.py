from rest_framework import status
from rest_framework.response import Response

from vendors.models import VendorServiceableLocation
from vendors.serializers import VendorServiceableLocationSerializer


class AddServiceableLocationHelper:
    def handle(self, request):
        serializer = VendorServiceableLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor = serializer.validated_data["vendor"]
        service_location = serializer.validated_data["service_location"]
        vendor_serviceable_location, created = VendorServiceableLocation.objects.get_or_create(
            vendor=vendor,
            service_location=service_location,
        )

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        response_serializer = VendorServiceableLocationSerializer(vendor_serviceable_location)
        return Response(response_serializer.data, status=response_status)
