from rest_framework import serializers
from .models import CalendarEvent

class CalendarEventSerializer(serializers.ModelSerializer):
    day_of_week = serializers.SerializerMethodField()

    class Meta:
        model = CalendarEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'event_type', 'related_appointment', 'user']

    def get_day_of_week(self, obj):
        return obj.date.strftime('%A') if obj.date else None

    def create(self, validated_data):
        # These values will be set explicitly in perform_create
        validated_data.pop('user', None)
        validated_data.pop('event_type', None)
        return CalendarEvent.objects.create(**validated_data)
