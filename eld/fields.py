from rest_framework import serializers
from geopy import Nominatim
from django.core.cache import cache
import re


class FlexibleLocationField(serializers.Field):
    """
    Handles location input in multiple formats:
    - "lat,lng" (e.g., "40.7128,-74.0060")
    - "City, State" (e.g., "New York, NY")
    """
    COORD_REGEX = r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$'

    def to_internal_value(self, value):
        # Check if value is coordinates
        if re.match(self.COORD_REGEX, value):
            lat, lng = map(float, value.split(','))
            return {
                'latitude': lat,
                'longitude': lng,
                'address': f"{lat},{lng}"
            }

        # Check cache
        cache_key = f"location_{value}"
        if cached := cache.get(cache_key):
            return cached

        # Geocode using Nominatim
        try:
            geolocator = Nominatim(user_agent="eld_system")
            location = geolocator.geocode(value)
            if not location:
                raise serializers.ValidationError("Could not geocode location")

            result = {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address
            }
            cache.set(cache_key, result, 60 * 60 * 24 * 7)  # Cache for 1 week
            return result

        except Exception as e:
            raise serializers.ValidationError(f"Geocoding error: {str(e)}")

    def to_representation(self, value):
        return {
            'coordinates': f"{value.latitude},{value.longitude}",
            'address': value.address
        }