from rest_framework import serializers
from .models import Appointment, AppointmentRequest

class AppointmentRequestSerializer(serializers.ModelSerializer):
    krisshak_email = serializers.CharField(source='krisshak.email', read_only=True)
    bhooswami_email = serializers.CharField(source='bhooswami.email', read_only=True)

    class Meta:
        model = AppointmentRequest
        fields = '__all__'
        read_only_fields = ['id', 'request_time', 'status']

class AppointmentSerializer(serializers.ModelSerializer):
    krisshak_email = serializers.CharField(source='krisshak.email', read_only=True)
    bhooswami_email = serializers.CharField(source='bhooswami.email', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'status']
