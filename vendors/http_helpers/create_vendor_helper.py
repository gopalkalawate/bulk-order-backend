from rest_framework import status
from rest_framework.response import Response

from vendors.serializers import VendorSerializer


class CreateVendorHelper:
    def handle(self, request):
        serializer = VendorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor = serializer.save()
        return Response(VendorSerializer(vendor).data, status=status.HTTP_201_CREATED)
