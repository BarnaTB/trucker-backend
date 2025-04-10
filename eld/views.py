from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from eld.models import ELDLog, Driver
from eld.serializers import ELDLogSerializer, DriverSerializer
from eld.exceptions import HOSViolation
from utils.decorators import hos_rate_limit
from django.utils.decorators import method_decorator


class ELDLogAPI(generics.ListCreateAPIView):
    """
    Endpoint: POST /api/eld/logs/
    Creates HOS-compliant log entries
    """

    # class ELDLogAPI(generics.ListCreateAPIView):
    serializer_class = ELDLogSerializer
    queryset = ELDLog.objects.all()

    @method_decorator(hos_rate_limit)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except HOSViolation as e:
            return Response(
                {"error": e.detail, "code": e.violation_type},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_queryset(self):
        return ELDLog.objects.filter(driver=self.request.user.driver)


class DriverAPI(APIView):
    """
    Endpoint: GET/PUT /api/eld/drivers/me/
    Manages driver profile
    """

    @hos_rate_limit
    def get(self, request):
        serializer = DriverSerializer(request.user.driver)
        return Response(serializer.data)

    @hos_rate_limit
    def put(self, request):
        serializer = DriverSerializer(
            request.user.driver,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)