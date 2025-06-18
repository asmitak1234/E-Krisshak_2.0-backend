from django.contrib import admin
from .models import CalendarEvent

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'date', 'time', 'event_type', 'related_appointment', 'created_at')
    list_filter = ('event_type', 'date', 'user')
    search_fields = ('title', 'description', 'user__email')
    ordering = ('-date', '-time')

