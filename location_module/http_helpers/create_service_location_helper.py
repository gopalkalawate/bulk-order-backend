from rest_framework import status
from rest_framework.response import Response

from location_module.serializers import ServiceLocationSerializer


class CreateServiceLocationHelper:
    def handle(self, request):
        serializer = ServiceLocationSerializer(data=request.data)
        if serializer.is_valid():
            service_location = serializer.save()
            return Response(ServiceLocationSerializer(service_location).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
