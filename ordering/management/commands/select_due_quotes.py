from django.core.management.base import BaseCommand
from django.utils import timezone
from ordering.models import OrderCycle
from ordering.services import select_lowest_quotes


class Command(BaseCommand):
    help = "Select lowest eligible quotes for cycles whose quote window has ended"

    def handle(self, *args, **options):
        for cycle_id in OrderCycle.objects.filter(status=OrderCycle.Status.QUOTING, quote_window_end__lte=timezone.now()).values_list("id", flat=True):
            select_lowest_quotes(cycle_id)
            self.stdout.write(f"Selected quotes for cycle {cycle_id}")
