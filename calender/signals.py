from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import CalendarEvent
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Appointment)
def create_or_update_calendar_event_from_appointment(sender, instance, created, **kwargs):
    try:
        if instance.status != 'confirmed':
            # Only act if the appointment is confirmed
            return

        # Handle case where either participant might be missing (edge safety)
        if not instance.krisshak or not instance.bhooswami:
            logger.warning("Confirmed appointment missing participants.")
            return

        title = f"Appointment with {instance.krisshak.email if instance.bhooswami else instance.bhooswami.email}"
        participants = [instance.krisshak, instance.bhooswami]

        for user in participants:
            event, created = CalendarEvent.objects.get_or_create(
                user=user,
                related_appointment=instance,
                defaults={
                    'title': title,
                    'description': "Auto-scheduled from appointment.",
                    'date': instance.date,
                    'time': instance.time,
                    'event_type': 'appointment',
                }
            )

            if not created:
                # Update existing event if date/time has changed
                if event.date != instance.date or event.time != instance.time:
                    event.date = instance.date
                    event.time = instance.time
                    event.save()
    except Exception as e:
        logger.error(f"Calendar event sync failed for Appointment ID {instance.id}: {str(e)}")
