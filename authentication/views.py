from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegistrationSerializer


class RegistrationAPI(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                "message": "Driver registered successfully",
                "driver_id": serializer.instance.driver.id,
                "license_number": serializer.instance.driver.license_number,
                "username": serializer.instance.username,
                "email": serializer.instance.email
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if request.user.is_authenticated:
            response.data.update({
                'driver_id': request.user.driver.id,
                'license_number': request.user.driver.license_number
            })
        return response
