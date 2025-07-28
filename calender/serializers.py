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
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['event_type'] = 'manual'
        return CalendarEvent.objects.create(**validated_data)
