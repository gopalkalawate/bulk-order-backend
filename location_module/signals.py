from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from config.cache_utils import bump_service_locations_cache_version
from location_module.models import ServiceLocation


@receiver(post_save, sender=ServiceLocation)
@receiver(post_delete, sender=ServiceLocation)
def invalidate_service_location_cache(sender, **kwargs):
    bump_service_locations_cache_version()
