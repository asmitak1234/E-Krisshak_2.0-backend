from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment
from notifications.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.mail import send_mail

channel_layer = get_channel_layer()

@receiver(post_save, sender=Payment)
def notify_payment(sender, instance, created, **kwargs):
    if instance.status != 'completed':
        return  # Notify only after success

    # Avoid double notifications
    if created or not instance.external_payment_id:
        return

    # Send notification to both sender and recipient
    for user in [instance.sender, instance.recipient]:
        title = "💸 Payment Received" if user == instance.recipient else "✅ Payment Sent"
        message = f"{instance.amount} INR for: {instance.purpose or 'payment'}"
        notif = Notification.objects.create(
            recipient=user,
            notification_type='payment',
            title=title,
            message=message
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "send.notification",
                "data": {
                    "title": notif.title,
                    "message": notif.message,
                    "timestamp": notif.created_at.isoformat()
                }
            }
        )

        # ✉️ Email both users
        if user.email:
            send_mail(
                subject=title,
                message=f"Hi {user.email},\n\n{message}\n\nThank you for using our platform.",
                from_email='payments@ekrisshak2.0emails.and.help@gmail.com',
                recipient_list=[user.email],
                fail_silently=True,
            )
