from django.db import models
from django.contrib.auth.models import User


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    current_cycle_hours = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"


class Vehicle(models.Model):
    vin = models.CharField(max_length=17, unique=True)
    eld_device_id = models.CharField(max_length=50)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)


class ELDLog(models.Model):
    STATUS_CHOICES = [
        ('OFF', 'Off Duty'),
        ('SB', 'Sleeper Berth'),
        ('D', 'Driving'),
        ('ON', 'On Duty')
    ]

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255)
    odometer = models.FloatField()
    remarks = models.TextField()
