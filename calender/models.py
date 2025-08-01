from django.db import models
from django.conf import settings
from appointments.models import Appointment

# Create your models here.

class CalendarEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('manual', 'Manual'),
        ('appointment', 'Appointment'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='manual')
    related_appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        unique_together = ('user', 'related_appointment')
        verbose_name = "Calendar Event"

    def __str__(self):
        email = getattr(self.user, 'email', 'Unknown')
        return f"{self.title} ({self.date}) - {email}"
