from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from .authentication import JWTAuthentication
from .http_helpers.create_user_helper import CreateUserHelper
from .http_helpers.get_user_helper import GetUserHelper
from .http_helpers.login_helper import LoginHelper
from .http_helpers.refresh_token_helper import RefreshTokenHelper
from .http_helpers.test_helper import TestHelper

# Create your views here.

@api_view(['POST'])
def create_user(request):
    return CreateUserHelper().handle(request)


@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_user(request):
    return GetUserHelper().handle(request)


@api_view(['POST'])
def login(request):
    return LoginHelper().handle(request)


@api_view(['POST'])
def get_access_token_from_refresh(request):
    return RefreshTokenHelper().handle(request)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def test(request):
    return TestHelper().handle(request)
