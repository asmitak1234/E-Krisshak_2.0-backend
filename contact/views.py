from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.core.mail import EmailMessage
from django.conf import settings
from .serializers import ContactMessageSerializer, NoticeSerializer
from .models import ContactMessage, Notice
from users.models import DistrictAdminProfile, StateAdminProfile, KrisshakProfile, BhooswamiProfile, CustomUser
from django.http import JsonResponse
from rest_framework.decorators import api_view


class ContactMessageListView(generics.ListAPIView):
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        base_qs = ContactMessage.objects.filter(parent__isnull=True)

        try:
            if user.is_superuser:
                return base_qs

            if user.user_type == 'state_admin':
                state = user.stateadminprofile.state
                return base_qs.filter(state=state)

            if user.user_type == 'district_admin':
                district = user.districtadminprofile.district
                return base_qs.filter(district=district)

            if user.user_type in ['krisshak', 'bhooswami']:
                sent = ContactMessage.objects.filter(sender=user, parent__isnull=True)
                replies = ContactMessage.objects.filter(parent__sender=user).exclude(sender=user)

                # Merge with Python, not .union()
                combined = list(sent) + list(replies)
                combined.sort(key=lambda x: x.created_at, reverse=True)  # newest first
                return combined

            return base_qs.filter(sender=user)

        except Exception as e:
            print("🔥 ContactMessageListView Error:", str(e))
            return ContactMessage.objects.none()


class ContactMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        user = request.user

        if serializer.is_valid():
            msg = ContactMessage(**serializer.validated_data)
            msg.sender = user
            msg.sender_type = user.user_type

            # Determine location context
            state = district = None
            if user.user_type == 'krisshak' and hasattr(user, 'krisshakprofile'):
                profile = user.krisshakprofile
                state, district = profile.state, profile.district
            elif user.user_type == 'bhooswami' and hasattr(user, 'bhooswamiprofile'):
                profile = user.bhooswamiprofile
                state, district = profile.state, profile.district
            elif user.user_type == 'district_admin':
                profile = user.districtadminprofile
                district = profile.district
                state = district.state if district else None
            elif user.user_type == 'state_admin':
                profile = user.stateadminprofile
                state = profile.state

            msg.state = state
            msg.district = district

            # Determine forward path
            forwarded_to = recipient_email = None
            if user.user_type in ['krisshak', 'bhooswami'] and district:
                try:
                    district_admin = DistrictAdminProfile.objects.get(district__name__iexact=district.name)
                    recipient_email = district_admin.user.email
                    forwarded_to = "District Admin"
                except DistrictAdminProfile.DoesNotExist:
                    pass
            elif user.user_type == 'district_admin' and state:
                try:
                    state_admin = StateAdminProfile.objects.get(state__name__iexact=state.name)
                    recipient_email = state_admin.user.email
                    forwarded_to = "State Admin"
                except StateAdminProfile.DoesNotExist:
                    pass
            elif user.user_type == 'state_admin':
                recipient_email = settings.ADMIN_EMAIL
                forwarded_to = "Superadmin"

            msg.forwarded_to = forwarded_to
            msg.save()

            # Send email
            try:
                email_body = f"""
                Name: {msg.name}
                Email: {msg.email}
                Subject: {msg.subject}

                Message:
                {msg.message}

                Forwarded To: {forwarded_to}
                """
                email = EmailMessage(
                    subject=f"[Ekrisshak Contact] {msg.subject}",
                    body=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email] if recipient_email else [settings.ADMIN_EMAIL],
                    reply_to=[msg.email],
                )
                email.send(fail_silently=False)
                return Response({"message": "Message sent successfully."}, status=200)
            except Exception as e:
                return Response({"error": str(e)}, status=500)

        return Response(serializer.errors, status=400)


class ContactReplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        parent_message = ContactMessage.objects.filter(id=pk).first()
        if not parent_message:
            return Response({"error": "Parent message not found."}, status=404)

        user = request.user
        reply = ContactMessage.objects.create(
            sender=user,
            sender_type=user.user_type,
            name=user.name or "Admin",
            email=user.email,
            subject=f"RE: {parent_message.subject}",
            message=request.data.get('message', ''),
            parent=parent_message,
            is_admin_reply=True,
            state=parent_message.state,
            district=parent_message.district
        )
        return Response({"message": "Reply saved successfully."}, status=201)


@api_view(["GET"])
def get_notices(request):
    """Fetch notices visible to the logged-in user."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        # Try to match user’s role safely
        if hasattr(user, "stateadminprofile"):
            state = user.stateadminprofile.state
            notices = Notice.objects.filter(state=user.stateadminprofile)
        elif hasattr(user, "districtadminprofile"):
            district = user.districtadminprofile
            notices = Notice.objects.filter(district=district)
        else:
            # fallback for Krisshak or others — filter by state via profile
            state = None
            if hasattr(user, "krisshakprofile"):
                state = user.krisshakprofile.state
            elif hasattr(user, "bhooswamiprofile"):
                state = user.bhooswamiprofile.state

            notices = Notice.objects.filter(state__state=state) if state else Notice.objects.none()

        serialized = NoticeSerializer(notices, many=True)
        return JsonResponse({"notices": serialized.data}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def create_notice(request):
    """Allows state or district admins to create a notice."""
    user = request.user
    if user.user_type not in ["state_admin", "district_admin"]:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    content = request.data.get("content")
    if not content:
        return JsonResponse({"error": "Notice content is required"}, status=400)

    notice = Notice.objects.create(
        author_type=user.user_type,
        state=user.stateadminprofile if user.user_type == "state_admin" else user.districtadminprofile.state,
        district=user.districtadminprofile if user.user_type == "district_admin" else None,
        content=content
    )

    # Live Notification Trigger
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "global_notice_updates",
        {
            "type": "send.notification",
            "data": {
                "title": "📢 New Notice Posted",
                "message": notice.content,
                "timestamp": notice.timestamp.isoformat(),
            },
        },
    )

    return JsonResponse({"message": "Notice created successfully"}, status=201)

class PublicContactMessageView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            msg = serializer.save(
                sender_type="guest",
                forwarded_to="Superadmin",
                state=None,
                district=None,
                parent=None,
                is_admin_reply=False,
                is_resolved=False
            )
            msg.sender_type = "guest"
            msg.forwarded_to = "Superadmin"
            msg.save()

            try:
                EmailMessage(
                    subject=f"[Public Contact] {msg.subject}",
                    body=f"""
                    Name: {msg.name}
                    Email: {msg.email}
                    Message:
                    {msg.message}
                    """,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[settings.EMAIL_HOST_USER],
                    reply_to=[msg.email],
                ).send(fail_silently=False)
            except Exception as e:
                print("❌ Email send error:", e)
                
            return Response({"message": "Thank you for reaching out!"}, status=200)
        return Response(serializer.errors, status=400)
