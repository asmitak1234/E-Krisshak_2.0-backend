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

    krisshak_user_id = serializers.SerializerMethodField()
    bhooswami_user_id = serializers.SerializerMethodField()

    def get_krisshak_user_id(self, obj):
        return obj.krisshak.id if obj.krisshak else None

    def get_bhooswami_user_id(self, obj):
        return obj.bhooswami.id if obj.bhooswami else None

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'status']
        extra_kwargs = {
                'bhooswami': {'required': False},
                'status': {'required': False},
                'created_at': {'read_only': True},
            }

