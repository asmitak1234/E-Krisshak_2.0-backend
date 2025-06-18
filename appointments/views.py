from users.models import KrisshakProfile, BhooswamiProfile
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.mail import EmailMessage
from .models import Appointment, AppointmentRequest
from .serializers import AppointmentSerializer
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.conf import settings
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from django.http import JsonResponse
from django.core.mail import send_mail

class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'krisshak':
            return Appointment.objects.filter(krisshak=user)

        elif user.user_type == 'bhooswami':
            return Appointment.objects.filter(bhooswami=user)

        elif user.user_type == 'district_admin':
            try:
                district = user.districtadminprofile.district
                krisshaks = KrisshakProfile.objects.filter(district=district).values_list('user_id', flat=True)
                bhooswamis = BhooswamiProfile.objects.filter(district=district).values_list('user_id', flat=True)
                return Appointment.objects.filter(krisshak_id__in=krisshaks, bhooswami_id__in=bhooswamis)
            except:
                return Appointment.objects.none()

        elif user.user_type == 'state_admin':
            try:
                state = user.stateadminprofile.state
                krisshaks = KrisshakProfile.objects.filter(state=state).values_list('user_id', flat=True)
                bhooswamis = BhooswamiProfile.objects.filter(state=state).values_list('user_id', flat=True)
                return Appointment.objects.filter(krisshak_id__in=krisshaks, bhooswami_id__in=bhooswamis)
            except:
                return Appointment.objects.none()

        return Appointment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.user_type != 'bhooswami':
            raise permissions.PermissionDenied("Only Bhooswamis can create appointments.")

        krisshak = serializer.validated_data.get('krisshak')
        krisshak_profile = getattr(krisshak, 'krisshakprofile', None)

        if not krisshak_profile or not krisshak_profile.availability:
            raise permissions.PermissionDenied("Selected Krisshak is currently unavailable.")

        appointment = serializer.save(bhooswami=user)
        self.send_appointment_pdf_email(appointment)


    def send_appointment_pdf_email(self, appointment):
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 750, "Appointment Confirmation")
        p.drawString(100, 720, f"Bhooswami: {appointment.bhooswami.email}")
        p.drawString(100, 700, f"Krisshak: {appointment.krisshak.email}")
        p.drawString(100, 680, f"Date: {appointment.date}")
        p.drawString(100, 660, f"Time: {appointment.time}")
        p.drawString(100, 640, f"Status: {appointment.status}")
        p.save()

        buffer.seek(0)
        pdf = buffer.getvalue()

        email = EmailMessage(
            "Appointment Confirmation",
            "Your appointment has been confirmed. Please find the attached PDF.",
            "ekrisshak2.0emails.and.help@gmail.com",
            [appointment.krisshak.email, appointment.bhooswami.email],
        )
        email.attach("appointment.pdf", pdf, "application/pdf")
        email.send()


class AppointmentRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        if 'status' not in request.data:
            return Response({"error": "Only status updates are allowed."}, status=status.HTTP_400_BAD_REQUEST)

        return self.partial_update(request, *args, **kwargs)


def request_appointment(request, bhooswami_id):
    """Krisshaks can request Bhooswamis for an appointment."""
    krisshak = request.user
    bhooswami = get_object_or_404(settings.AUTH_USER_MODEL, id=bhooswami_id)

    existing_request = AppointmentRequest.objects.filter(krisshak=krisshak, bhooswami=bhooswami, status='pending').order_by('-request_time').first()
    if existing_request and not existing_request.is_expired():
        return JsonResponse({"error": "Request already sent. Try again after 2 days."}, status=400)

    appointment_request = AppointmentRequest.objects.create(krisshak=krisshak, bhooswami=bhooswami, status='pending')

    send_mail(
        subject="New Appointment Request",
        message=f"{krisshak.email} has requested an appointment. You can review it in your Requests section.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[bhooswami.email]
    )

    return JsonResponse({"message": "Request sent successfully."})


def get_requests(request):
    """Fetch pending requests."""
    user = request.user
    if hasattr(user, 'krisshakprofile'):
        requests = AppointmentRequest.objects.filter(krisshak=user, status='pending')
    elif hasattr(user, 'bhooswamiprofile'):
        requests = AppointmentRequest.objects.filter(bhooswami=user, status='pending')
    else:
        return JsonResponse({"error": "Profile not found."}, status=404)

    return JsonResponse({"requests": [req.krisshak.email if hasattr(user, 'bhooswamiprofile') else req.bhooswami.email for req in requests]})
