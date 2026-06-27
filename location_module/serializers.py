from rest_framework import serializers
from .models import ServiceLocation, UserServiceLocation
from django.contrib.gis.geos import Point


class ServiceLocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = ServiceLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def create(self, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['point'] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)


class NearbyServiceLocationSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = ServiceLocation
        fields = ['id', 'name', 'distance_km', 'is_active']

    def get_distance_km(self, obj):
        return round(obj.distance_km, 2) if hasattr(obj, 'distance_km') else None


class UserServiceLocationSerializer(serializers.ModelSerializer):
    service_location_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceLocation.objects.filter(is_active=True),
        source='service_location',
        write_only=True,
    )
    service_location = NearbyServiceLocationSerializer(read_only=True)

    class Meta:
        model = UserServiceLocation
        fields = ['id', 'service_location_id', 'service_location', 'created_at']
        read_only_fields = ['id', 'service_location', 'created_at']
