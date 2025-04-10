from rest_framework import serializers
from django.contrib.auth.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    license_number = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'license_number']

    def create(self, validated_data):
        license_number = validated_data.pop('license_number')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        # Driver creation moved to eld app signals
        return user
