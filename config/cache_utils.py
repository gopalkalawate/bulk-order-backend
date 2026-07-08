from django.conf import settings
from django.core.cache import cache


DEFAULT_VERSION = 1
SERVICE_LOCATIONS_VERSION_KEY = "service_locations:cache_version"


def get_cache_value(key):
    return cache.get(key)


def set_cache_value(key, value, timeout=None):
    if timeout is None:
        timeout = settings.DEFAULT_CACHE_TTL
    cache.set(key, value, timeout=timeout)


def get_or_set_cache_version(version_key):
    version = cache.get(version_key)
    if version is None:
        version = DEFAULT_VERSION
        cache.set(version_key, version, timeout=None)
    return version


def bump_cache_version(version_key):
    get_or_set_cache_version(version_key)
    try:
        return cache.incr(version_key)
    except ValueError:
        version = DEFAULT_VERSION + 1
        cache.set(version_key, version, timeout=None)
        return version


def get_vendor_cache_version_key(vendor_id):
    return f"vendor:{vendor_id}:cache_version"


def bump_vendor_cache_version(vendor_id):
    return bump_cache_version(get_vendor_cache_version_key(vendor_id))


def bump_service_locations_cache_version():
    return bump_cache_version(SERVICE_LOCATIONS_VERSION_KEY)


def build_vendor_service_locations_cache_key(vendor_id, radius_km=20):
    vendor_version = get_or_set_cache_version(get_vendor_cache_version_key(vendor_id))
    service_location_version = get_or_set_cache_version(SERVICE_LOCATIONS_VERSION_KEY)
    return f"vendor:{vendor_id}:service_locations:r{radius_km}:v{vendor_version}:slv{service_location_version}"
