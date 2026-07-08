from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from users.authentication import JWTAuthentication
from .http_helpers.create_item_category_helper import CreateItemCategoryHelper
from .http_helpers.create_item_helper import CreateItemHelper
from .http_helpers.search_items_helper import SearchItemsHelper
from .http_helpers.update_item_helper import UpdateItemHelper


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_item_category(request):
    return CreateItemCategoryHelper().handle(request)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_item(request):
    return CreateItemHelper().handle(request)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def search_items(request):
    return SearchItemsHelper().handle(request)


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_item(request, item_id):
    return UpdateItemHelper().handle(request, item_id)
