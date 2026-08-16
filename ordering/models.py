from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from items.models import Item
from location_module.models import ServiceLocation
from vendors.models import Vendor


class OrderCycle(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        QUOTING = "quoting", "Quoting"
        VENDOR_SELECTED = "vendor_selected", "Vendor selected"
        PLACED = "placed", "Placed"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    service_location = models.ForeignKey(ServiceLocation, on_delete=models.PROTECT, related_name="order_cycles")
    cycle_date = models.DateField()
    order_window_start = models.DateTimeField()
    order_window_end = models.DateTimeField()
    quote_window_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_cycles"
        constraints = [models.UniqueConstraint(fields=["service_location", "cycle_date"], name="unique_cycle_location_date")]
        indexes = [models.Index(fields=["service_location", "status"])]


class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CHECKED_OUT = "checked_out", "Checked out"
        ABANDONED = "abandoned", "Abandoned"

    cycle = models.ForeignKey(OrderCycle, on_delete=models.PROTECT, related_name="carts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="carts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"
        constraints = [models.UniqueConstraint(fields=["cycle", "user"], condition=Q(status="active"), name="one_active_cart_per_user_cycle")]


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_items"
        constraints = [models.UniqueConstraint(fields=["cart", "item"], name="unique_cart_item")]


class UserOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    cycle = models.ForeignKey(OrderCycle, on_delete=models.PROTECT, related_name="user_orders")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_orders"


class UserOrderItem(models.Model):
    user_order = models.ForeignKey(UserOrder, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "user_order_items"
        constraints = [models.UniqueConstraint(fields=["user_order", "item"], name="unique_user_order_item")]


class AggregatedOrderItem(models.Model):
    cycle = models.ForeignKey(OrderCycle, on_delete=models.PROTECT, related_name="aggregated_items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    total_quantity = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    selected_quote_item = models.OneToOneField("VendorQuoteItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="selected_for")

    class Meta:
        db_table = "aggregated_order_items"
        constraints = [models.UniqueConstraint(fields=["cycle", "item"], name="unique_aggregated_item")]


class VendorQuote(models.Model):
    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        SUBMITTED = "submitted", "Submitted"
        REJECTED = "rejected", "Rejected"
        PARTIALLY_SELECTED = "partially_selected", "Partially selected"
        SELECTED = "selected", "Selected"

    cycle = models.ForeignKey(OrderCycle, on_delete=models.PROTECT, related_name="vendor_quotes")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="quotes")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.INVITED)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vendor_quotes"
        constraints = [models.UniqueConstraint(fields=["cycle", "vendor"], name="unique_vendor_quote_cycle")]


class VendorQuoteItem(models.Model):
    quote = models.ForeignKey(VendorQuote, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    available_quantity = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])

    class Meta:
        db_table = "vendor_quote_items"
        constraints = [models.UniqueConstraint(fields=["quote", "item"], name="unique_vendor_quote_item")]


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        IN_TRANSIT = "in_transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    cycle = models.ForeignKey(OrderCycle, on_delete=models.PROTECT, related_name="purchase_orders")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    placed_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "purchase_orders"
        constraints = [models.UniqueConstraint(fields=["cycle", "vendor"], name="unique_po_cycle_vendor")]


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    aggregated_order_item = models.OneToOneField(AggregatedOrderItem, on_delete=models.PROTECT, related_name="purchase_order_item")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = "purchase_order_items"

    @property
    def line_total(self):
        return self.quantity * self.unit_price
