from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .services import RoutePlanner
from routes.serializers import RouteRequestSerializer


class RouteAPI(APIView):
    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        planner = RoutePlanner(settings.ORS_API_KEY)
        route = planner.get_route(
            start=serializer.validated_data['start_coords'],
            end=serializer.validated_data['end_coords']
        )

        # Add human-readable addresses to response
        route.update({
            'start_address': serializer.validated_data['start_address'],
            'end_address': serializer.validated_data['end_address']
        })

        return Response(route)
