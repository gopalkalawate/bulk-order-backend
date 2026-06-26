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
from location_module.views import create_service_location, get_service_location

urlpatterns = [
    # path('admin/', admin.site.urls), # django admin is disabled for this project
    path('auth/create_user', create_user, name='create_user'),
    path('auth/get_user', get_user, name='get_user'),
    path('auth/login', login, name='login'),
    path('auth/test', test, name='test'),
    path('auth/refresh', get_access_token_from_refresh, name='get_access_token_from_refresh'),
    path('admin/create-service-location', create_service_location, name='create_service_location'),
    path('get_service_location', get_service_location, name='get_service_location'),
]
