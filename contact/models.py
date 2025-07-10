from django.db import models
from django.conf import settings
from users.models import State, District, StateAdminProfile, DistrictAdminProfile,CustomUser

class ContactMessage(models.Model):
    SENDER_TYPE_CHOICES = [
        ('krisshak', 'Krisshak'),
        ('bhooswami', 'Bhooswami'),
        ('district_admin', 'District Admin'),
        ('state_admin', 'State Admin'),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    # Optional chaining
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    is_admin_reply = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)

    # Location context
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)

    forwarded_to = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contact Message"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or 'System'} - {self.subject}"


class Notice(models.Model):
    author_type = models.CharField(max_length=20, choices=[("state_admin", "State Admin"), ("district_admin", "District Admin")])
    author_name = models.CharField(max_length=255)  # Stores formatted author name
    state = models.ForeignKey(StateAdminProfile, on_delete=models.CASCADE, related_name="state_notices")
    district = models.ForeignKey(DistrictAdminProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="district_notices")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Automatically format author_name based on admin type."""
        if self.author_type == "state_admin":
            self.author_name = f"State Admin ({self.state.state.state_name})"
        elif self.author_type == "district_admin":
            self.author_name = f"District Admin ({self.district.district.district_name}, {self.state.state.state_name})"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-timestamp"]  # ✅ Ensures latest notices appear first
