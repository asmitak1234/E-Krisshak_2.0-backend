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
