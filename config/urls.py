"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users.views import *
from location_module.views import create_service_location, get_service_location, set_user_service_location
from vendors.views import (
    add_serviceable_location,
    create_vendor,
    get_service_locations,
    remove_serviceable_location,
    set_vendor_location,
)
from items.views import create_item, create_item_category, search_items, update_item

urlpatterns = [
    # path('admin/', admin.site.urls), # django admin is disabled for this project
    path('auth/create_user', create_user, name='create_user'),
    path('auth/get_user', get_user, name='get_user'),
    path('auth/login', login, name='login'),
    path('auth/test', test, name='test'),
    path('auth/refresh', get_access_token_from_refresh, name='get_access_token_from_refresh'),
    path('admin/create-service-location', create_service_location, name='create_service_location'),
    path('get_service_location', get_service_location, name='get_service_location'),
    path('set_user_service_location', set_user_service_location, name='set_user_service_location'),
    path('vendors/create_vendor', create_vendor, name='create_vendor'),
    path('vendors/set-vendor-location', set_vendor_location, name='set_vendor_location'),
    path('vendors/get-service-locations', get_service_locations, name='get_vendor_service_locations'),
    path('vendors/add-serviceable-location', add_serviceable_location, name='add_serviceable_location'),
    path('vendors/remove-serviceable-location', remove_serviceable_location, name='remove_serviceable_location'),
    path('items/create-category', create_item_category, name='create_item_category'),
    path('items/create-item', create_item, name='create_item'),
    path('items/search', search_items, name='search_items'),
    path('items/<int:item_id>', update_item, name='update_item'),
]
