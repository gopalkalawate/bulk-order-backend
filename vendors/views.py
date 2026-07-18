from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from users.authentication import JWTAuthentication
from .http_helpers.add_serviceable_location_helper import AddServiceableLocationHelper
from .http_helpers.create_vendor_helper import CreateVendorHelper
from .http_helpers.get_vendor_service_locations_helper import GetVendorServiceLocationsHelper
from .http_helpers.remove_serviceable_location_helper import RemoveServiceableLocationHelper
from .http_helpers.set_vendor_location_helper import SetVendorLocationHelper
from .models import Vendor, VendorItem
from .serializers import LinkVendorPartnerSerializer, VendorItemSerializer
from ordering.permissions import IsAdminRole


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


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminRole])
def link_vendor_partner(request, vendor_id):
    vendor = Vendor.objects.filter(id=vendor_id, is_active=True).first()
    if not vendor:
        return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = LinkVendorPartnerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    vendor.partner_user = serializer.validated_data["partner_user"]
    vendor.save(update_fields=["partner_user"])
    return Response({"vendor_id": vendor.id, "partner_user_id": str(vendor.partner_user_id)})


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminRole])
def add_vendor_item(request, vendor_id):
    vendor = Vendor.objects.filter(id=vendor_id, is_active=True).first()
    if not vendor:
        return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = VendorItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    vendor_item, created = VendorItem.objects.get_or_create(vendor=vendor, item=serializer.validated_data["item"])
    return Response(VendorItemSerializer(vendor_item).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminRole])
def remove_vendor_item(request, vendor_id, item_id):
    deleted, _ = VendorItem.objects.filter(vendor_id=vendor_id, item_id=item_id).delete()
    if not deleted:
        return Response({"error": "Vendor item not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)
