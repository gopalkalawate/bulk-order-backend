from rest_framework import status
from rest_framework.response import Response

from location_module.models import UserServiceLocation
from location_module.serializers import UserServiceLocationSerializer


class SetUserServiceLocationHelper:
    def handle(self, request):
        serializer = UserServiceLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service_location = serializer.validated_data['service_location']
        user_service_location, created = UserServiceLocation.objects.update_or_create(
            user=request.user,
            defaults={'service_location': service_location},
        )

        response_serializer = UserServiceLocationSerializer(user_service_location)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=response_status)
