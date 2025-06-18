from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import CalendarEvent

@receiver(post_save, sender=Appointment)
def create_or_update_calendar_event_from_appointment(sender, instance, created, **kwargs):
    if instance.status == 'confirmed':  # Ensure event creation only for confirmed appointments
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
                event.date = instance.date
                event.time = instance.time
                event.save()
