from users.models import KrisshakProfile, BhooswamiProfile
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.mail import EmailMessage
from .models import Appointment, AppointmentRequest
from .serializers import AppointmentSerializer, AppointmentRequestSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.conf import settings
import json
from django.db.models import Q
from io import BytesIO
from reportlab.pdfgen import canvas
from django.http import JsonResponse
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type in ['krisshak', 'bhooswami']:
            return Appointment.objects.filter(
                Q(krisshak=user) | Q(bhooswami=user)
            ).order_by('-date', '-time')


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def request_appointment(request, user_id):
    sender = request.user
    User = get_user_model()
    recipient = get_object_or_404(User, id=user_id)

    if sender == recipient:
        return JsonResponse({"error": "You cannot send a request to yourself."}, status=400)

    existing_request = AppointmentRequest.objects.filter(
        sender=sender, recipient=recipient, status='pending'
    ).order_by('-request_time').first()

    if existing_request and not existing_request.is_expired():
        return JsonResponse({"error": "Request already sent. Try again after 2 days."}, status=400)

    AppointmentRequest.objects.create(sender=sender, recipient=recipient)

    send_mail(
        subject="New Appointment Request",
        message=f"{sender.email} has requested an appointment with you.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient.email],
    )

    return JsonResponse({"message": "Appointment request sent."})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_requests(request):
    user = request.user
    sent = AppointmentRequest.objects.filter(sender=user).order_by("-request_time")
    received = AppointmentRequest.objects.filter(recipient=user).order_by("-request_time")

    return Response({
        "sent_requests": AppointmentRequestSerializer(sent, many=True).data,
        "received_requests": AppointmentRequestSerializer(received, many=True).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_request(request, request_id):
    try:
        appt_request = AppointmentRequest.objects.get(id=request_id)
    except AppointmentRequest.DoesNotExist:
        return Response({"error": "Request not found."}, status=404)

    if appt_request.status != 'pending':
        return Response({"error": "Request already handled."}, status=400)

    user = request.user
    if user != appt_request.recipient:
        return Response({"error": "You are not authorized to accept this request."}, status=403)

    appt_request.status = 'accepted'
    appt_request.save()

    # Determine who is the krisshak/bhooswami based on roles
    if appt_request.sender.user_type == 'krisshak':
        krisshak, bhooswami = appt_request.sender, appt_request.recipient
    else:
        krisshak, bhooswami = appt_request.recipient, appt_request.sender

    appointment = Appointment.objects.create(
        krisshak=krisshak,
        bhooswami=bhooswami,
        date=now().date(),
        time=now().time(),
        status='confirmed',
        payment_status='not_paid'
    )

    send_mail(
        subject="Appointment Confirmed",
        message=f"Appointment between {krisshak.email} and {bhooswami.email} is confirmed for today.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[krisshak.email, bhooswami.email]
    )

    return Response({
        "message": "Request accepted and appointment confirmed.",
        "appointment": AppointmentSerializer(appointment).data
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancel_request(request, request_id):
    try:
        appt_request = AppointmentRequest.objects.get(id=request_id)
    except AppointmentRequest.DoesNotExist:
        return Response({"error": "Request not found."}, status=404)

    user = request.user
    if appt_request.sender != user and appt_request.recipient != user:
        return Response({"error": "You are not authorized to cancel this request."}, status=403)

    appt_request.delete()
    return Response({"message": "Request canceled successfully."}, status=204)
