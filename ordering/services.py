from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from vendors.models import VendorItem
from .models import (
    AggregatedOrderItem, Cart, OrderCycle, PurchaseOrder, PurchaseOrderItem,
    UserOrder, UserOrderItem, VendorQuote,
)


def ensure_ordering_open(cycle):
    now = timezone.now()
    if cycle.status != OrderCycle.Status.OPEN or not (cycle.order_window_start <= now < cycle.order_window_end):
        raise ValidationError("The ordering window is not open")


@transaction.atomic
def checkout_cart(cycle_id, user):
    cycle = OrderCycle.objects.select_for_update().get(pk=cycle_id)
    ensure_ordering_open(cycle)
    cart = Cart.objects.select_for_update().filter(cycle=cycle, user=user, status=Cart.Status.ACTIVE).first()
    if not cart:
        raise ValidationError("No active cart exists for this cycle")
    cart_items = list(cart.items.select_related("item").all())
    if not cart_items:
        raise ValidationError("The cart is empty")
    order = UserOrder.objects.create(
        cycle=cycle,
        user=user,
        cart=cart,
        status=UserOrder.Status.CONFIRMED,
    )
    UserOrderItem.objects.bulk_create([
        UserOrderItem(user_order=order, item=line.item, quantity=line.quantity, notes=line.notes)
        for line in cart_items
    ])
    cart.status = Cart.Status.CHECKED_OUT
    cart.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def close_cycle(cycle_id):
    cycle = OrderCycle.objects.select_for_update().select_related("service_location").get(pk=cycle_id)
    if cycle.status != OrderCycle.Status.OPEN:
        raise ValidationError("Only open cycles can be closed")
    totals = (
        UserOrderItem.objects.filter(user_order__cycle=cycle, user_order__status=UserOrder.Status.CONFIRMED)
        .values("item_id").annotate(total_quantity=Sum("quantity"))
    )
    AggregatedOrderItem.objects.bulk_create([
        AggregatedOrderItem(cycle=cycle, item_id=row["item_id"], total_quantity=row["total_quantity"])
        for row in totals
    ], ignore_conflicts=True)
    item_ids = list(cycle.aggregated_items.values_list("item_id", flat=True))
    eligible_vendor_ids = VendorItem.objects.filter(
        item_id__in=item_ids,
        vendor__is_active=True,
        vendor__serviceable_locations__service_location=cycle.service_location,
    ).values_list("vendor_id", flat=True).distinct()
    VendorQuote.objects.bulk_create(
        [VendorQuote(cycle=cycle, vendor_id=vendor_id) for vendor_id in eligible_vendor_ids],
        ignore_conflicts=True,
    )
    cycle.status = OrderCycle.Status.QUOTING
    cycle.save(update_fields=["status"])
    return cycle


@transaction.atomic
def select_lowest_quotes(cycle_id):
    cycle = OrderCycle.objects.select_for_update().get(pk=cycle_id)
    if cycle.status not in [OrderCycle.Status.QUOTING, OrderCycle.Status.VENDOR_SELECTED]:
        raise ValidationError("Quotes can only be selected while a cycle is quoting")
    selected = []
    unquoted = []
    aggregate_items = cycle.aggregated_items.select_for_update().filter(selected_quote_item__isnull=True).select_related("item")
    for aggregate in aggregate_items:
        candidates = (
            aggregate.item.vendorquoteitem_set.filter(
                quote__cycle=cycle,
                quote__status=VendorQuote.Status.SUBMITTED,
            ).filter(
                Q(available_quantity__isnull=True) | Q(available_quantity__gte=aggregate.total_quantity)
            ).select_related("quote__vendor").order_by("unit_price", "id")
        )
        winner = candidates.first()
        if not winner:
            unquoted.append(aggregate.item_id)
            continue
        aggregate.selected_quote_item = winner
        aggregate.save(update_fields=["selected_quote_item"])
        po, _ = PurchaseOrder.objects.get_or_create(cycle=cycle, vendor=winner.quote.vendor)
        PurchaseOrderItem.objects.get_or_create(
            aggregated_order_item=aggregate,
            defaults={"purchase_order": po, "quantity": aggregate.total_quantity, "unit_price": winner.unit_price},
        )
        selected.append(aggregate.item_id)

    for po in PurchaseOrder.objects.filter(cycle=cycle).prefetch_related("items"):
        po.total_amount = sum((line.line_total for line in po.items.all()), Decimal("0"))
        po.save(update_fields=["total_amount"])
    selected_quote_ids = cycle.aggregated_items.exclude(selected_quote_item__isnull=True).values_list("selected_quote_item__quote_id", flat=True)
    VendorQuote.objects.filter(cycle=cycle, status=VendorQuote.Status.SUBMITTED).exclude(id__in=selected_quote_ids).update(status=VendorQuote.Status.REJECTED)
    for quote in VendorQuote.objects.filter(cycle=cycle, id__in=selected_quote_ids):
        count = quote.items.filter(selected_for__isnull=False).count()
        quote.status = VendorQuote.Status.SELECTED if count == quote.items.count() else VendorQuote.Status.PARTIALLY_SELECTED
        quote.save(update_fields=["status"])
    if not cycle.aggregated_items.filter(selected_quote_item__isnull=True).exists():
        cycle.status = OrderCycle.Status.VENDOR_SELECTED
        cycle.save(update_fields=["status"])
    return {"cycle": cycle, "selected_item_ids": selected, "unquoted_item_ids": unquoted}
