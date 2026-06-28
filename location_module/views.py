from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from users.authentication import JWTAuthentication
from .http_helpers.create_service_location_helper import CreateServiceLocationHelper
from .http_helpers.get_service_location_helper import GetServiceLocationHelper
from .http_helpers.set_user_service_location_helper import SetUserServiceLocationHelper


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_service_location(request):
    return CreateServiceLocationHelper().handle(request)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_service_location(request):
    return GetServiceLocationHelper().handle(request)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_user_service_location(request):
    return SetUserServiceLocationHelper().handle(request)
