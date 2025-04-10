import requests
from django.core.cache import cache


class RoutePlanner:
    ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
    FUEL_STOP_INTERVAL = 1000  # miles

    def __init__(self, api_key):
        self.api_key = api_key

    def get_route(self, start, end):
        # print(f"Calculating route from {start} to {end}")
        start_lng, start_lat = start[1], start[0]
        end_lng, end_lat = end[1], end[0]

        params = {
            'api_key': self.api_key,
            'start': f"{start_lng},{start_lat}",
            'end': f"{end_lng},{end_lat}"
        }

        response = requests.get(self.ORS_BASE_URL, params=params)

        print(f"Request URL: {response.url}")
        print(f"Request Response: {response.json()}")
        if response.status_code != 200:
            raise ValueError("Route calculation failed")

        data = response.json()
        return self._process_route(data)

    def _process_route(self, data):
        feature = data['features'][0]
        properties = feature['properties']
        geometry = feature['geometry']
        segments = properties['segments'][0]

        distance_miles = segments['distance'] / 1609.34  # meters to miles
        duration_hours = segments['duration'] / 3600  # seconds to hours

        return {
            'geometry': geometry,
            'distance': round(distance_miles, 2),
            'duration': round(duration_hours, 2),
            'fuel_stops': self._calculate_fuel_stops(distance_miles),
            'steps': self._build_steps(
                api_steps=segments['steps'],
                geometry_coords=geometry['coordinates'],
                total_distance=distance_miles
            )
        }

    def _calculate_fuel_stops(self, distance):
        return [{'mile': (i + 1) * self.FUEL_STOP_INTERVAL}
                for i in range(int(distance // self.FUEL_STOP_INTERVAL))]

    def _build_steps(self, api_steps, geometry_coords, total_distance):
        steps = []
        fuel_stops = self._calculate_fuel_stops(total_distance)
        fuel_stop_index = 0
        cumulative_miles = 0.0

        for step in api_steps:
            # Convert API step data
            step_miles = step['distance'] / 1609.34  # meters to miles
            step_hours = step['duration'] / 3600  # seconds to hours

            # Get coordinates from geometry
            start_idx = step['way_points'][0]
            end_idx = step['way_points'][1]
            start_coord = geometry_coords[start_idx]
            end_coord = geometry_coords[end_idx]

            # Add driving step
            steps.append({
                'type': 'driving',
                'instruction': step.get('instruction', 'Continue'),
                'distance': round(step_miles, 2),
                'duration': round(step_hours, 2),
                'start': {
                    'coordinates': [start_coord[0], start_coord[1]],
                    'address': self._get_nearest_city(start_coord[1], start_coord[0])
                },
                'end': {
                    'coordinates': [end_coord[0], end_coord[1]],
                    'address': self._get_nearest_city(end_coord[1], end_coord[0])
                }
            })

            # Check for fuel stops within this segment
            while fuel_stop_index < len(fuel_stops):
                next_stop = fuel_stops[fuel_stop_index]
                if next_stop['mile'] > cumulative_miles + step_miles:
                    break

                # Calculate position within this step
                stop_position = next_stop['mile'] - cumulative_miles
                position_ratio = stop_position / step_miles

                # Interpolate coordinates
                stop_lng = start_coord[0] + (end_coord[0] - start_coord[0]) * position_ratio
                stop_lat = start_coord[1] + (end_coord[1] - start_coord[1]) * position_ratio

                # Add fuel stop
                steps.append({
                    'type': 'fuel',
                    'mile': next_stop['mile'],
                    'location': {
                        'coordinates': [stop_lng, stop_lat],
                        'address': self._get_nearest_city(stop_lat, stop_lng)
                    },
                    'duration': 0.5
                })
                fuel_stop_index += 1

            cumulative_miles += step_miles

        return steps

    def _get_nearest_city(self, lat, lng):
        """Simplified reverse geocoding using cached data"""
        # In production, use a proper reverse geocoding service
        return f"{lat:.4f}, {lng:.4f}"