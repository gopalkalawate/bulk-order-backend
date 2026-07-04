from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from users.authentication import JWTAuthentication
from .http_helpers.add_serviceable_location_helper import AddServiceableLocationHelper
from .http_helpers.create_vendor_helper import CreateVendorHelper
from .http_helpers.get_vendor_service_locations_helper import GetVendorServiceLocationsHelper
from .http_helpers.remove_serviceable_location_helper import RemoveServiceableLocationHelper
from .http_helpers.set_vendor_location_helper import SetVendorLocationHelper


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_vendor(request):
    return CreateVendorHelper().handle(request)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_vendor_location(request):
    return SetVendorLocationHelper().handle(request)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_service_locations(request):
    return GetVendorServiceLocationsHelper().handle(request)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_serviceable_location(request):
    return AddServiceableLocationHelper().handle(request)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_serviceable_location(request):
    return RemoveServiceableLocationHelper().handle(request)
