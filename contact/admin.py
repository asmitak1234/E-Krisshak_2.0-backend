from django.contrib import admin
from .models import ContactMessage, Notice
from django.core.mail import EmailMessage
from django.conf import settings
from users.models import DistrictAdminProfile, StateAdminProfile

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'sender_type', 'state', 'district', 'subject', 'forwarded_to', 'created_at')
    list_filter = ('sender_type', 'state', 'district', 'forwarded_to', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        obj.sender = request.user
        obj.sender_type = getattr(request.user, 'user_type', None)

        # Forwarding logic
        state = obj.state
        district = obj.district
        forwarded_to = None
        recipient_email = None

        if obj.sender_type in ['krisshak', 'bhooswami'] and district:
            try:
                district_admin = DistrictAdminProfile.objects.get(district__name__iexact=district.name)
                recipient_email = district_admin.user.email
                forwarded_to = "District Admin"
            except DistrictAdminProfile.DoesNotExist:
                pass

        elif obj.sender_type == 'district_admin' and state:
            try:
                state_admin = StateAdminProfile.objects.get(state__name__iexact=state.name)
                recipient_email = state_admin.user.email
                forwarded_to = "State Admin"
            except StateAdminProfile.DoesNotExist:
                pass

        elif obj.sender_type == 'state_admin':
            recipient_email = settings.ADMIN_EMAIL
            forwarded_to = "Superadmin"

        if forwarded_to:
            obj.forwarded_to = forwarded_to

        super().save_model(request, obj, form, change)

        # Only send email for new messages
        if is_new:
            try:
                email_body = f"""
                Name: {obj.name}
                Email: {obj.email}
                Subject: {obj.subject}

                Message:
                {obj.message}

                Forwarded To: {forwarded_to or '—'}
                """
                email = EmailMessage(
                    subject=f"[Ekrisshak Contact] {obj.subject}",
                    body=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email] if recipient_email else [settings.ADMIN_EMAIL],
                    reply_to=[obj.email],
                )
                email.send(fail_silently=False)
            except Exception as e:
                self.message_user(request, f"Message saved, but failed to send email: {str(e)}", level='error')


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ["author_name", "content", "timestamp"]
    search_fields = ["author_name", "content"]
