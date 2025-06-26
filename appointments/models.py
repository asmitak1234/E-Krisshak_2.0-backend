from django.db import models
from django.conf import settings
import uuid
from datetime import timedelta
from django.utils.timezone import now

class AppointmentRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('expired', 'Expired')], default='pending')
    request_time = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.request_time + timedelta(days=2)

    class Meta:
        verbose_name = "Appointment Request"

class Appointment(models.Model):
    """Stores confirmed appointments between Krisshaks & Bhooswamis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    krisshak = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='krisshak_appointments')
    bhooswami = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bhooswami_appointments')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed')], default='pending')
    payment_status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('not_paid', 'Not Paid')], default='not_paid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment: {self.bhooswami.email} ↔ {self.krisshak.email}"
