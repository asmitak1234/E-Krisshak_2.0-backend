from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from calender.models import CalendarEvent
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Sends reminders for upcoming calendar events'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        upcoming = now + timedelta(hours=1)

        events = CalendarEvent.objects.filter(
            date=upcoming.date(),
            time__hour=upcoming.time().hour,
            time__minute=upcoming.time().minute,
            event_type='manual'
        )

        for event in events:
            already_notified = Notification.objects.filter(
                recipient=event.user,
                notification_type='calendar',
                title__icontains=event.title,
                message__icontains='in 1 hour'
            ).exists()

            if not already_notified:
                Notification.objects.create(
                    recipient=event.user,
                    notification_type='calendar',
                    title=f"⏰ Reminder: '{event.title}' in 1 hour",
                    message=f"Scheduled for {event.date.strftime('%A, %b %d')} at {event.time.strftime('%I:%M %p')}."
                )

        self.stdout.write(self.style.SUCCESS(f"Processed {events.count()} upcoming events"))
