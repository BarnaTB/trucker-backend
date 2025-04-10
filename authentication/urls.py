from django.urls import path
from authentication.views import RegistrationAPI, CustomTokenObtainPairView

urlpatterns = [
    path('register/', RegistrationAPI.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
]
