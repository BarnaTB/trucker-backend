from rest_framework import serializers
from eld.models import Driver, ELDLog
from eld.fields import FlexibleLocationField
from eld.exceptions import HOSViolation
from eld.services import HOSValidator


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'name', 'license_number', 'current_cycle_hours']
        read_only_fields = ['current_cycle_hours']


class ELDLogSerializer(serializers.ModelSerializer):
    location = FlexibleLocationField(source='*')
    start_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    end_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = ELDLog
        fields = [
            'id', 'driver', 'start_time', 'end_time',
            'status', 'location', 'remarks', 'odometer'
        ]
        read_only_fields = ['driver', 'location_name']
        extra_kwargs = {
            'driver': {'read_only': True}
        }

    def validate(self, data):
        # Check time order
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")

        # Check HOS compliance
        driver = self.context['request'].user.driver
        validator = HOSValidator(driver)

        try:
            validator.check_driving_segment(
                data['end_time'] - data['start_time'],
                data['status']
            )
        except HOSViolation as e:
            raise serializers.ValidationError(str(e))

        return data

    def create(self, validated_data):
        driver = self.context['request'].user.driver
        return ELDLog.objects.create(driver=driver, **validated_data)