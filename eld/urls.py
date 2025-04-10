from django.urls import path
from .views import ELDLogAPI, DriverAPI

urlpatterns = [
    path('logs/', ELDLogAPI.as_view(), name='eld-logs'),
    path('drivers/me/', DriverAPI.as_view(), name='driver-detail'),
]
