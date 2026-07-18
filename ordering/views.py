from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from location_module.models import UserServiceLocation
from users.authentication import JWTAuthentication
from .models import Cart, CartItem, OrderCycle, PurchaseOrder, UserOrder, VendorQuote, VendorQuoteItem
from .permissions import IsAdminRole, IsVendorPartner
from .serializers import CartItemSerializer, CartSerializer, CycleSerializer, PurchaseOrderSerializer, QuoteItemInputSerializer, QuoteSerializer, UserOrderSerializer
from .services import checkout_cart, close_cycle, ensure_ordering_open, select_lowest_quotes


def user_location(user):
    relation = UserServiceLocation.objects.filter(user=user, service_location__is_active=True).select_related("service_location").first()
    if not relation:
        raise ValidationError("User does not have an active service location")
    return relation.service_location


def ensure_customer(user):
    if user.role != "CUSTOMER":
        raise PermissionDenied("Only customer accounts can manage carts and orders")


def customer_cycle(cycle_id, user):
    cycle = OrderCycle.objects.select_related("service_location").filter(pk=cycle_id).first()
    if not cycle:
        raise NotFound("Order cycle not found")
    if user.role != "ADMIN" and cycle.service_location_id != user_location(user).id:
        raise PermissionDenied("This cycle is not available at your service location")
    return cycle


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminRole])
def create_order_cycle(request):
    serializer = CycleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cycle = serializer.save()
    return Response(CycleSerializer(cycle).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def current_order_cycle(request):
    ensure_customer(request.user)
    location = user_location(request.user)
    now = timezone.now()
    cycle = OrderCycle.objects.filter(service_location=location, status=OrderCycle.Status.OPEN, order_window_start__lte=now, order_window_end__gt=now).order_by("order_window_end").first()
    if not cycle:
        return Response({"detail": "No open order cycle"}, status=status.HTTP_404_NOT_FOUND)
    return Response(CycleSerializer(cycle).data)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def order_cycle_detail(request, cycle_id):
    cycle = customer_cycle(cycle_id, request.user)
    return Response(CycleSerializer(cycle).data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminRole])
def close_order_cycle(request, cycle_id):
    cycle = close_cycle(cycle_id)
    return Response(CycleSerializer(cycle).data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsAdminRole])
def select_cycle_quotes(request, cycle_id):
    result = select_lowest_quotes(cycle_id)
    return Response({"cycle": CycleSerializer(result["cycle"]).data, "selected_item_ids": result["selected_item_ids"], "unquoted_item_ids": result["unquoted_item_ids"]})


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cart_detail(request, cycle_id):
    cycle = customer_cycle(cycle_id, request.user)
    cart = Cart.objects.filter(cycle=cycle, user=request.user, status=Cart.Status.ACTIVE).prefetch_related("items").first()
    if not cart:
        return Response({"cycle_id": cycle.id, "status": "active", "items": []})
    return Response(CartSerializer(cart).data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_cart_item(request, cycle_id):
    ensure_customer(request.user)
    cycle = customer_cycle(cycle_id, request.user)
    ensure_ordering_open(cycle)
    serializer = CartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(cycle=cycle, user=request.user, status=Cart.Status.ACTIVE)
        line, created = CartItem.objects.update_or_create(cart=cart, item=serializer.validated_data["item"], defaults={"quantity": serializer.validated_data["quantity"], "notes": serializer.validated_data.get("notes", "")})
    return Response(CartItemSerializer(line).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["PATCH", "DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_cart_item(request, cycle_id, item_id):
    ensure_customer(request.user)
    cycle = customer_cycle(cycle_id, request.user)
    ensure_ordering_open(cycle)
    line = CartItem.objects.filter(cart__cycle=cycle, cart__user=request.user, cart__status=Cart.Status.ACTIVE, item_id=item_id).first()
    if not line:
        raise NotFound("Cart item not found")
    if request.method == "DELETE":
        line.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = CartItemSerializer(line, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def checkout(request, cycle_id):
    ensure_customer(request.user)
    customer_cycle(cycle_id, request.user)
    order = checkout_cart(cycle_id, request.user)
    return Response(UserOrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def orders(request):
    ensure_customer(request.user)
    queryset = UserOrder.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
    cycle_id = request.query_params.get("cycle_id")
    if cycle_id:
        queryset = queryset.filter(cycle_id=cycle_id)
    return Response(UserOrderSerializer(queryset, many=True).data)


def partner_quote(quote_id, user):
    quote = VendorQuote.objects.prefetch_related("items").filter(pk=quote_id).first()
    if not quote:
        raise NotFound("Vendor quote not found")
    if user.role != "ADMIN" and quote.vendor.partner_user_id != user.id:
        raise PermissionDenied("This quote does not belong to your vendor")
    return quote


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsVendorPartner])
def vendor_quotes(request):
    quotes = VendorQuote.objects.filter(vendor__partner_user=request.user).prefetch_related("items").order_by("-created_at")
    return Response(QuoteSerializer(quotes, many=True).data)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsVendorPartner])
def vendor_quote_detail(request, quote_id):
    return Response(QuoteSerializer(partner_quote(quote_id, request.user)).data)


@api_view(["PUT"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsVendorPartner])
def set_quote_items(request, quote_id):
    quote = partner_quote(quote_id, request.user)
    if quote.status != VendorQuote.Status.INVITED or timezone.now() >= quote.cycle.quote_window_end:
        raise ValidationError("This quote can no longer be edited")
    serializer = QuoteItemInputSerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)
    invited_item_ids = set(quote.cycle.aggregated_items.values_list("item_id", flat=True))
    eligible_item_ids = set(quote.vendor.vendor_items.values_list("item_id", flat=True))
    for line in serializer.validated_data:
        if line["item"].id not in invited_item_ids or line["item"].id not in eligible_item_ids:
            raise ValidationError("Quoted items must be aggregated items your vendor is eligible to supply")
    with transaction.atomic():
        quote.items.all().delete()
        VendorQuoteItem.objects.bulk_create([VendorQuoteItem(quote=quote, **line) for line in serializer.validated_data])
    quote.refresh_from_db()
    return Response(QuoteSerializer(quote).data)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsVendorPartner])
def submit_quote(request, quote_id):
    quote = partner_quote(quote_id, request.user)
    if quote.status != VendorQuote.Status.INVITED or timezone.now() >= quote.cycle.quote_window_end:
        raise ValidationError("This quote can no longer be submitted")
    if not quote.items.exists():
        raise ValidationError("A quote requires at least one item")
    quote.status = VendorQuote.Status.SUBMITTED
    quote.submitted_at = timezone.now()
    quote.save(update_fields=["status", "submitted_at"])
    return Response(QuoteSerializer(quote).data)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def purchase_orders(request):
    queryset = PurchaseOrder.objects.prefetch_related("items").order_by("-placed_at")
    if request.user.role == "ADMIN":
        pass
    elif request.user.role == "PARTNER" and hasattr(request.user, "vendor_profile"):
        queryset = queryset.filter(vendor=request.user.vendor_profile)
    else:
        raise PermissionDenied("Purchase orders are available only to administrators and linked vendors")
    if request.query_params.get("cycle_id"):
        queryset = queryset.filter(cycle_id=request.query_params["cycle_id"])
    return Response(PurchaseOrderSerializer(queryset, many=True).data)
