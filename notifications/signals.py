from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from notifications.models import Notification
from appointments.models import Appointment
from contact.models import ContactMessage, Notice
from calender.models import CalendarEvent
from appointments.models import AppointmentRequest
from redis.exceptions import ConnectionError
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

# 📡 Helper function to safely send WebSocket notifications
def send_ws_notification(group: str, data: dict):
    try:
        async_to_sync(channel_layer.group_send)(
            group,
            {
                "type": "send.notification",
                "data": data,
            },
        )
    except ConnectionError as e:
        logging.error(f"Redis group_send failed for group '{group}': {str(e)}")

# 🔔 New Appointment Notification
@receiver(post_save, sender=Appointment)
def notify_appointment(sender, instance, created, **kwargs):
    if instance.status == 'confirmed':
        for user in [instance.krisshak, instance.bhooswami]:
            notif = Notification.objects.create(
                recipient=user,
                sender=instance.bhooswami or instance.krisshak,
                notification_type='appointment',
                title="📅 Appointment Confirmed",
                message=f"You have a confirmed appointment on {instance.date.strftime('%b %d')} at {instance.time.strftime('%I:%M %p')}"
            )
            send_ws_notification(f"user_{user.id}", {
                "title": notif.title,
                "message": notif.message,
                "timestamp": notif.created_at.isoformat(),
            })

# 💬 Contact Message / Reply Notification
@receiver(post_save, sender=ContactMessage)
def notify_contact(sender, instance, created, **kwargs):
    if not created or instance.sender_type == "guest":
        return

    if instance.parent:
        notif = Notification.objects.create(
            recipient=instance.parent.sender,
            sender=instance.sender,
            notification_type='contact',
            title="Reply Received",
            message=f"Someone responded to your message: {instance.subject}",
        )
        if notif.recipient:
            send_ws_notification(f"user_{notif.recipient.id}", {
                "title": notif.title,
                "message": notif.message,
                "timestamp": notif.created_at.isoformat(),
            })

    elif instance.forwarded_to and instance.sender:
        notif = Notification.objects.create(
            recipient=instance.sender,
            notification_type='contact',
            title="Message Forwarded",
            message=f"Your message '{instance.subject}' has been forwarded to {instance.forwarded_to}.",
        )
        if notif.recipient:
            send_ws_notification(f"user_{notif.recipient.id}", {
                "title": notif.title,
                "message": notif.message,
                "timestamp": notif.created_at.isoformat(),
            })

# 📅 Calendar Event Created Notification
@receiver(post_save, sender=CalendarEvent)
def notify_calendar_event(sender, instance, created, **kwargs):
    if created and instance.event_type == 'manual':
        notif = Notification.objects.create(
            recipient=instance.user,
            notification_type='calendar',
            title="📌 Calendar Event Added",
            message=f"{instance.title} on {instance.date.strftime('%A, %b %d')} at {instance.time.strftime('%I:%M %p')}.",
        )
        send_ws_notification(f"user_{notif.recipient.id}", {
            "title": notif.title,
            "message": notif.message,
            "timestamp": notif.created_at.isoformat(),
        })

# ⏰ Upcoming Event Reminder
@receiver(post_save, sender=CalendarEvent)
def notify_upcoming_event(sender, instance, **kwargs):
    event_time = instance.time
    now_time = now().time()
    if instance.date == now().date() and event_time.hour - now_time.hour == 1:
        notif = Notification.objects.create(
            recipient=instance.user,
            notification_type='event_reminder',
            title="⏰ Upcoming Event Reminder",
            message=f"Reminder: {instance.title} starts at {event_time.strftime('%I:%M %p')}.",
        )
        send_ws_notification(f"user_{notif.recipient.id}", {
            "title": notif.title,
            "message": notif.message,
            "timestamp": notif.created_at.isoformat(),
        })

# 📢 New Notice Notification
@receiver(post_save, sender=Notice)
def notify_new_notice(sender, instance, created, **kwargs):
    if created:
        notif = Notification.objects.create(
            recipient=None,
            notification_type="notice",
            title="📢 New Notice Posted",
            message=instance.content,
        )
        send_ws_notification("global_notice_updates", {
            "title": notif.title,
            "message": notif.message,
            "timestamp": notif.created_at.isoformat(),
        })

# 🔔 Appointment Request Notification
@receiver(post_save, sender=AppointmentRequest)
def notify_appointment_request(sender, instance, created, **kwargs):
    if not created:
        return

    recipient = instance.recipient
    sender_user = instance.sender
    role = "Krisshak" if sender_user.user_type == "krisshak" else "Bhooswami"

    notif = Notification.objects.create(
        recipient=recipient,
        sender=sender_user,
        notification_type="requests",
        title="🔔 New Appointment Request",
        message=f"{sender_user.name} ({role}) has requested an appointment.",
    )
    send_ws_notification(f"user_{recipient.id}", {
        "title": notif.title,
        "message": notif.message,
        "timestamp": notif.created_at.isoformat(),
    })
