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

        if user.is_superuser:
            return ContactMessage.objects.all()

        if user.user_type == 'state_admin':
            try:
                state = user.stateadminprofile.state
                return ContactMessage.objects.filter(state=state)
            except:
                return ContactMessage.objects.none()

        if user.user_type == 'district_admin':
            try:
                district = user.districtadminprofile.district
                return ContactMessage.objects.filter(district=district)
            except:
                return ContactMessage.objects.none()

        return ContactMessage.objects.filter(sender=user)


class ContactMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        user = request.user

        if serializer.is_valid():
            msg = serializer.save(commit=False)
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

    # Fetch notices only for the user’s state
    notices = Notice.objects.filter(state=user.stateadminprofile.state)
    serialized_notices = NoticeSerializer(notices, many=True).data

    return JsonResponse({"notices": serialized_notices}, safe=False)

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
