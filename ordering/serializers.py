from decimal import Decimal

from rest_framework import serializers
from items.models import Item
from location_module.models import ServiceLocation
from .models import Cart, CartItem, OrderCycle, PurchaseOrder, PurchaseOrderItem, UserOrder, UserOrderItem, VendorQuote, VendorQuoteItem


class CycleSerializer(serializers.ModelSerializer):
    service_location_id = serializers.PrimaryKeyRelatedField(queryset=ServiceLocation.objects.filter(is_active=True), source="service_location")

    class Meta:
        model = OrderCycle
        fields = ["id", "service_location_id", "cycle_date", "order_window_start", "order_window_end", "quote_window_end", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        if not (attrs["order_window_start"] < attrs["order_window_end"] < attrs["quote_window_end"]):
            raise serializers.ValidationError("order_window_start must be before order_window_end, which must be before quote_window_end")
        return attrs


class CartItemSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.filter(is_active=True), source="item")

    class Meta:
        model = CartItem
        fields = ["item_id", "quantity", "notes", "added_at", "updated_at"]
        read_only_fields = ["added_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ["id", "cycle_id", "status", "items", "created_at", "updated_at"]


class UserOrderItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = UserOrderItem
        fields = ["item_id", "quantity", "notes"]


class UserOrderSerializer(serializers.ModelSerializer):
    items = UserOrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = UserOrder
        fields = ["id", "cycle_id", "status", "created_at", "items"]


class QuoteItemInputSerializer(serializers.Serializer):
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.filter(is_active=True), source="item")
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    available_quantity = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"), required=False, allow_null=True)


class QuoteItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = VendorQuoteItem
        fields = ["id", "item_id", "unit_price", "available_quantity"]


class QuoteSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True, read_only=True)
    class Meta:
        model = VendorQuote
        fields = ["id", "cycle_id", "vendor_id", "status", "submitted_at", "items"]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    class Meta:
        model = PurchaseOrderItem
        fields = ["aggregated_order_item_id", "quantity", "unit_price", "line_total"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = PurchaseOrder
        fields = ["id", "cycle_id", "vendor_id", "status", "placed_at", "total_amount", "items"]
