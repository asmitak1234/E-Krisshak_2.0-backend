from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from notifications.models import Notification
from appointments.models import Appointment
from contact.models import ContactMessage, Notice
from calender.models import CalendarEvent
from appointments.models import AppointmentRequest

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

# 🔔 New Appointment Notification
@receiver(post_save, sender=Appointment)
def notify_appointment(sender, instance, created, **kwargs):
    if instance.status == 'confirmed':  # ✅ Only notify when appointment is confirmed
        for user in [instance.krisshak, instance.bhooswami]:
            notif = Notification.objects.create(
                recipient=user,
                sender=instance.bhooswami if instance.bhooswami else instance.krisshak, # ✅ Ensure the correct sender is set
                notification_type='appointment',
                title="📅 Appointment Confirmed",
                message=f"You have a confirmed appointment on {instance.date.strftime('%b %d')} at {instance.time.strftime('%I:%M %p')}"
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "send.notification",
                    "data": {
                        "title": notif.title,
                        "message": notif.message,
                        "timestamp": notif.created_at.isoformat(),
                    },
                },
            )


# 💬 Contact Message / Reply Notification
@receiver(post_save, sender=ContactMessage)
def notify_contact(sender, instance, created, **kwargs):
    if created:
        # Reply to existing message
        if instance.parent:
            notif = Notification.objects.create(
                recipient=instance.parent.sender,
                sender=instance.sender,
                notification_type='contact',
                title="Reply Received",
                message=f"Someone responded to your message: {instance.subject}",
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{notif.recipient.id}",
                {
                    "type": "send.notification",
                    "data": {
                        "title": notif.title,
                        "message": notif.message,
                        "timestamp": notif.created_at.isoformat(),
                    },
                },
            )

        # New message forwarded
        elif instance.forwarded_to:
            notif = Notification.objects.create(
                recipient=instance.sender,
                notification_type='contact',
                title="Message Forwarded",
                message=f"Your message '{instance.subject}' has been forwarded to {instance.forwarded_to}.",
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{notif.recipient.id}",
                {
                    "type": "send.notification",
                    "data": {
                        "title": notif.title,
                        "message": notif.message,
                        "timestamp": notif.created_at.isoformat(),
                    },
                },
            )

# 🔔 Instant Notification When an 📆 Calendar Event is Created
@receiver(post_save, sender=CalendarEvent)
def notify_calendar_event(sender, instance, created, **kwargs):
    if created and instance.event_type == 'manual':
        notif = Notification.objects.create(
            recipient=instance.user,
            notification_type='calendar',
            title="📌 Calendar Event Added",
            message=f"{instance.title} on {instance.date.strftime('%A, %b %d')} at {instance.time.strftime('%I:%M %p')}.",
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{notif.recipient.id}",
            {
                "type": "send.notification",
                "data": {
                    "title": notif.title,
                    "message": notif.message,
                    "timestamp": notif.created_at.isoformat(),
                },
            },
        )

# ⏰ **Upcoming Event Reminder Logic**
@receiver(post_save, sender=CalendarEvent)
def notify_upcoming_event(sender, instance, **kwargs):
    """Send reminders 1 hour before an event starts."""
    event_time = instance.time
    now_time = now().time()

    # Check if the event is happening within the next hour
    if instance.date == now().date() and event_time.hour - now_time.hour == 1:
        notif = Notification.objects.create(
            recipient=instance.user,
            notification_type='event_reminder',
            title="⏰ Upcoming Event Reminder",
            message=f"Reminder: {instance.title} starts at {event_time.strftime('%I:%M %p')}.",
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{notif.recipient.id}",
            {
                "type": "send.notification",
                "data": {
                    "title": notif.title,
                    "message": notif.message,
                    "timestamp": notif.created_at.isoformat(),
                },
            },
        )


# 📢 **Trigger Live Notification When a Notice is Created**
@receiver(post_save, sender=Notice)
def notify_new_notice(sender, instance, created, **kwargs):
    """Sends real-time notification when a new notice is posted."""
    if created:
        notif = Notification.objects.create(
            recipient=None,  # Broadcast to all relevant users
            notification_type="notice",
            title="📢 New Notice Posted",
            message=instance.content,
        )

        async_to_sync(channel_layer.group_send)(
            "global_notice_updates",
            {
                "type": "send.notification",
                "data": {
                    "title": notif.title,
                    "message": notif.message,
                    "timestamp": notif.created_at.isoformat(),
                },
            },
        )


# 🔔 **Trigger Notification When a New Appointment Request is Created**
@receiver(post_save, sender=AppointmentRequest)
def notify_appointment_request(sender, instance, created, **kwargs):
    if not created:
        return

    recipient = instance.recipient
    sender_user = instance.sender

    # Optional: Customize the message based on who the recipient is
    role = "Krisshak" if sender_user.user_type == "krisshak" else "Bhooswami"

    notif = Notification.objects.create(
        recipient=recipient,
        sender=sender_user,
        notification_type="requests",
        title="🔔 New Appointment Request",
        message=f"{sender_user.name} ({role}) has requested an appointment.",
    )

    async_to_sync(channel_layer.group_send)(
        f"user_{recipient.id}",
        {
            "type": "send.notification",
            "data": {
                "title": notif.title,
                "message": notif.message,
                "timestamp": notif.created_at.isoformat(),
            },
        },
    )

