from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.response import Response

from location_module.models import ServiceLocation
from location_module.serializers import NearbyServiceLocationSerializer


class GetServiceLocationHelper:
    def handle(self, request):
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
