from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from users.authentication import JWTAuthentication
from .models import ServiceLocation, UserServiceLocation
from .serializers import NearbyServiceLocationSerializer, ServiceLocationSerializer, UserServiceLocationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes




@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_service_location(request):
    serializer = ServiceLocationSerializer(data=request.data)
    if serializer.is_valid():
        service_location = serializer.save()
        return Response(ServiceLocationSerializer(service_location).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_service_location(request):
    latitude = request.query_params.get('latitude')
    longitude = request.query_params.get('longitude')
    limit = request.query_params.get('limit', 5)

    if not latitude or not longitude:
        return Response({'error': 'latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        limit = int(limit)
    except ValueError:
        return Response({'error': 'latitude, longitude and limit must be numeric'}, status=status.HTTP_400_BAD_REQUEST)

    user_point = Point(longitude, latitude, srid=4326)
    nearby_locations = (
        ServiceLocation.objects.filter(is_active=True)
        .annotate(distance_km=Distance('point', user_point) * 111.3195)
        .order_by('distance_km')[:limit]
    )

    serializer = NearbyServiceLocationSerializer(nearby_locations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_user_service_location(request):
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
