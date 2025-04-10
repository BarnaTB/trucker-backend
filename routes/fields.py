from rest_framework import serializers
from django.core.cache import cache
from geopy import Nominatim
import re

class FlexibleLocationField(serializers.Field):
    """
    Handles location input in multiple formats:
    - Coordinates: "lat,lng" (e.g., "40.7128,-74.0060")
    - Place names: "City, State" (e.g., "New York, NY")
    """
    COORD_REGEX = r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$'

    def to_internal_value(self, value):
        # Check if input is coordinates
        if re.match(self.COORD_REGEX, value):
            lat, lng = map(float, value.split(','))
            return {
                'coordinates': (lat, lng),
                'address': f"{lat},{lng}"
            }

        # Check cache
        cache_key = f"route_location_{value}"
        if cached := cache.get(cache_key):
            return cached

        # Geocode place name
        geolocator = Nominatim(user_agent="eld_routes")
        location = geolocator.geocode(value)
        if not location:
            raise serializers.ValidationError(f"Could not geocode location: {value}")

        result = {
            'coordinates': (location.latitude, location.longitude),
            'address': location.address
        }
        cache.set(cache_key, result, 60*60*24*7)  # Cache for 1 week
        return result

    def to_representation(self, value):
        return value
