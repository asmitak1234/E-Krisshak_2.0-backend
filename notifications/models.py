from django.db import models
from django.conf import settings

# Create your models here.

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('appointment', 'Appointment'),
        ('contact', 'Contact'),
        ('calendar', 'Calender'),
        ('payment', 'Payment'),
        ('requests', 'Requests'),
        ('system', 'System'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] To: {self.recipient.email}"
