from django.apps import AppConfig


class LocationModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'location_module'

    def ready(self):
        import location_module.signals  # noqa: F401
