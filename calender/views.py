from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import CalendarEvent
from .serializers import CalendarEventSerializer
from appointments.models import Appointment
from users.models import KrisshakProfile, BhooswamiProfile

class CalendarEventListCreateView(generics.ListCreateAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CalendarEvent.objects.all()

        try:
            if user.user_type == 'state_admin':
                state = user.stateadminprofile.state
                krisshaks = list(KrisshakProfile.objects.filter(state=state).values_list('user_id', flat=True))
                bhooswamis = list(BhooswamiProfile.objects.filter(state=state).values_list('user_id', flat=True))
                return CalendarEvent.objects.filter(user_id__in=krisshaks + bhooswamis)

            elif user.user_type == 'district_admin':
                district = user.districtadminprofile.district
                krisshaks = list(KrisshakProfile.objects.filter(district=district).values_list('user_id', flat=True))
                bhooswamis = list(BhooswamiProfile.objects.filter(district=district).values_list('user_id', flat=True))
                return CalendarEvent.objects.filter(user_id__in=krisshaks + bhooswamis)

        except Exception:
            return CalendarEvent.objects.none()

        return CalendarEvent.objects.filter(user=user)

    def perform_create(self, serializer):
        try:
            serializer.save()  # No need to pass user/event_type here anymore
        except Exception as e:
            import logging
            logging.error(f"Calendar creation failed: {str(e)}")
            raise

class CalendarEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.event_type == 'appointment':
            return Response({"error": "Appointment-linked events cannot be edited."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
