from django.core.management.base import BaseCommand
from django.utils import timezone
from ordering.models import OrderCycle
from ordering.services import close_cycle


class Command(BaseCommand):
    help = "Close open cycles whose ordering window has ended"

    def handle(self, *args, **options):
        for cycle_id in OrderCycle.objects.filter(status=OrderCycle.Status.OPEN, order_window_end__lte=timezone.now()).values_list("id", flat=True):
            close_cycle(cycle_id)
            self.stdout.write(f"Closed cycle {cycle_id}")
