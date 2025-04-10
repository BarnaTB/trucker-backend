from rest_framework import serializers
from routes.fields import FlexibleLocationField


class RouteRequestSerializer(serializers.Serializer):
    start = FlexibleLocationField(required=True)
    end = FlexibleLocationField(required=True)

    def validate(self, data):
        """Convert locations to coordinate tuples"""
        return {
            'start_coords': data['start']['coordinates'],
            'end_coords': data['end']['coordinates'],
            'start_address': data['start']['address'],
            'end_address': data['end']['address']
        }
