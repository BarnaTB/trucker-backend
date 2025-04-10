from datetime import datetime, timedelta
from .exceptions import HOSViolation


class HOSValidator:
    def __init__(self, driver):
        self.driver = driver
        self.driving_time = timedelta()
        self.on_duty_time = timedelta()
        self.last_break = None

    def check_driving_segment(self, duration: timedelta, status: str):
        if status == 'D':
            # 11-hour driving limit
            if self.driving_time + duration > timedelta(hours=11):
                raise HOSViolation("11-hour driving limit exceeded", violation_type="11_hour_limit")

            # 14-hour duty window
            if self.on_duty_time + duration > timedelta(hours=14):
                raise HOSViolation("14-hour duty period exceeded", violation_type="14_hour_duty")

            # 30-minute break requirement
            if self.driving_time >= timedelta(hours=8):
                if not self.last_break or (datetime.now() - self.last_break) > duration:
                    raise HOSViolation("30-minute break required", violation_type="30_min_break")

            self.driving_time += duration
            self.on_duty_time += duration


class ELDGenerator:
    def __init__(self, driver):
        self.driver = driver
        self.validator = HOSValidator(driver)
        self.logs = []

    def generate_logs(self, route_data):
        timeline = []
        current_time = datetime.fromisoformat(route_data['start_time'])
        driver = self.driver
        remaining_driving = timedelta(hours=11)
        duty_start = None

        # 1. Mandatory 10-hour pre-trip rest
        timeline.append(self._create_log_entry(current_time, current_time + timedelta(hours=10), 'OFF',
                                               "Pre-trip rest period", route_data['start_location']))
        current_time += timedelta(hours=10)

        # 2. Pickup activities (1 hour On Duty)
        timeline.append(self._create_log_entry(
            current_time,
            current_time + timedelta(hours=1),
            'ON',
            "Loading cargo at pickup location",
            route_data['pickup_location']
        ))
        current_time += timedelta(hours=1)
        duty_start = current_time
        on_duty_time = timedelta(hours=1)

        # 3. Process route segments
        cumulative_driving = timedelta()
        for segment in route_data['steps']:
            if segment['type'] == 'driving':
                segment_duration = timedelta(hours=segment['duration'])
                segment_remaining = segment_duration

                while segment_remaining.total_seconds() > 0:
                    # Calculate available driving time before next break
                    available_driving = min(remaining_driving, timedelta(hours=8) - cumulative_driving,
                                             timedelta(hours=14) - on_duty_time, segment_remaining)

                    if available_driving.total_seconds() <= 0:
                        # Need to take a break before continuing
                        break_duration = timedelta(minutes=30)
                        timeline.append(self._create_log_entry(current_time, current_time + break_duration, 'OFF',
                                                               "Mandatory 30-minute break",
                                                               segment['location']))
                        current_time += break_duration
                        cumulative_driving = timedelta()
                        remaining_driving -= available_driving
                        continue

                    # Add driving segment
                    timeline.append(self._create_log_entry(current_time, current_time + available_driving,
                                                           'D', f"Driving {segment['distance']} miles",
                                                           segment['location']))
                    current_time += available_driving
                    cumulative_driving += available_driving
                    on_duty_time += available_driving
                    remaining_driving -= available_driving
                    segment_remaining -= available_driving

                    # Check HOS limits
                    self._check_hos_limits(on_duty_time=on_duty_time, driving_time=cumulative_driving,
                                           current_time=current_time, timeline=timeline)

            elif segment['type'] == 'fuel_stop':
                # Fuel stop (On Duty Not Driving)
                stop_duration = timedelta(minutes=30)
                timeline.append(self._create_log_entry(current_time, current_time + stop_duration, 'ON',
                                                       "Fueling stop", segment['location']))
                current_time += stop_duration
                on_duty_time += stop_duration
                self._check_hos_limits(on_duty_time=on_duty_time, driving_time=cumulative_driving,
                                       current_time=current_time, timeline=timeline)

        # 4. Dropoff activities (1 hour On Duty)
        timeline.append(self._create_log_entry(current_time, current_time + timedelta(hours=1), 'ON',
                                                "Unloading cargo at dropoff",
                                               route_data['dropoff_location']))
        current_time += timedelta(hours=1)
        on_duty_time += timedelta(hours=1)

        # 5. Split into daily logs
        daily_logs = self._split_daily_logs(timeline)

        return {
            'logs': daily_logs,
            'hos_summary': {
                'remaining_drive_time': remaining_driving.total_seconds() / 3600,
                'remaining_duty_hours': (timedelta(hours=14) - on_duty_time).total_seconds() / 3600,
                'cycle_hours_used': driver.current_cycle_hours + (on_duty_time.total_seconds() / 3600)
            }
        }

    def _check_hos_limits(self, on_duty_time, driving_time, current_time, timeline):
        """
        Validate HOS compliance at current timeline position
        :param on_duty_time: Total on-duty time accumulated so far
        :param driving_time: Total driving time accumulated so far
        :param current_time: Current timestamp in the timeline
        :param timeline: List of all log entries created so far
        """
        # 11-hour driving limit (395.3(a))
        if driving_time > timedelta(hours=11):
            raise HOSViolation("11-hour driving limit exceeded", violation_type="11_hour_limit")

        # 14-hour duty window (395.3(b))
        if on_duty_time > timedelta(hours=14):
            raise HOSViolation("14-hour duty period exceeded", violation_type="14_hour_duty")

        # 30-minute break requirement (395.3(a)(3)(ii))
        if driving_time >= timedelta(hours=8):
            # Find last break in timeline
            last_break = next((
                entry for entry in reversed(timeline)
                if entry['status'] in ('OFF', 'SB')
            ), None)

            if not last_break or \
                    (current_time - datetime.fromisoformat(last_break['end_time'])) > timedelta(hours=8):
                raise HOSViolation("30-minute break required after 8 hours driving",
                                   violation_type="30_min_break")

    def _create_log_entry(self, start, end, status, remarks, location):
        return {
            'start_time': start.isoformat(),
            'end_time': end.isoformat(),
            'status': status,
            'remarks': remarks,
            'location': location,
            'odometer': None  # Would be calculated from route data
        }

    def _split_daily_logs(self, timeline):
        daily_logs = {}
        for entry in timeline:
            date = datetime.fromisoformat(entry['start_time']).date()
            if date not in daily_logs:
                daily_logs[date] = []
            daily_logs[date].append(entry)

        return [{
            'date': str(date),
            'entries': entries,
            'totals': self._calculate_daily_totals(entries)
        } for date, entries in daily_logs.items()]

    def _calculate_daily_totals(self, entries):
        """
        Calculate daily totals for each duty status in 0.25 hour (15-minute) increments
        Returns: {
            'driving': float,
            'on_duty': float,
            'off_duty': float,
            'sleeper_berth': float
        }
        """
        totals = {
            'driving': 0.0,
            'on_duty': 0.0,
            'off_duty': 0.0,
            'sleeper_berth': 0.0
        }

        status_map = {
            'D': 'driving',
            'ON': 'on_duty',
            'OFF': 'off_duty',
            'SB': 'sleeper_berth'
        }

        for entry in entries:
            # Parse datetimes and calculate duration
            start = datetime.fromisoformat(entry['start_time'])
            end = datetime.fromisoformat(entry['end_time'])
            duration = end - start

            # Convert to hours and round to nearest 0.25 (15 minutes)
            hours = duration.total_seconds() / 3600
            rounded_hours = round(hours * 4) / 4  # Round to nearest 15 minutes

            # Add to appropriate total
            status_key = status_map.get(entry['status'], 'off_duty')
            totals[status_key] += rounded_hours

        # Ensure totals don't exceed 24 hours
        daily_total = sum(totals.values())
        if daily_total > 24:
            adjustment_factor = 24 / daily_total
            for key in totals:
                totals[key] = round(totals[key] * adjustment_factor, 2)

        return {k: round(v, 2) for k, v in totals.items()}
