from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    TYPE_CHOICES = [
        ('primary', 'Primary Payment'),
        ('tip', 'Appreciation Tip'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_payments')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255, help_text="What is this payment for?", blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='primary')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    external_payment_id = models.CharField(max_length=128, blank=True, null=True)  # Razorpay/UPI ref
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        kind = "Tip" if self.type == 'tip' else "Payment"
        return f"{kind} of ₹{self.amount} from {self.sender} to {self.recipient} - {self.status}"

    def is_tip(self):
        return self.type == 'tip'

    def mark_completed(self, transaction_id=None):
        self.status = 'completed'
        if transaction_id:
            self.external_payment_id = transaction_id
        self.save()
