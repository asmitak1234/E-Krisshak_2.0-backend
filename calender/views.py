from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
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

        if user.user_type == 'state_admin':
            try:
                state = user.stateadminprofile.state
                krisshaks = list(KrisshakProfile.objects.filter(state=state).values_list('user_id', flat=True))
                bhooswamis = list(BhooswamiProfile.objects.filter(state=state).values_list('user_id', flat=True))
                return CalendarEvent.objects.filter(user_id__in=krisshaks + bhooswamis)
            except:
                return CalendarEvent.objects.none()

        if user.user_type == 'district_admin':
            try:
                district = user.districtadminprofile.district
                krisshaks = list(KrisshakProfile.objects.filter(district=district).values_list('user_id', flat=True))
                bhooswamis = list(BhooswamiProfile.objects.filter(district=district).values_list('user_id', flat=True))
                return CalendarEvent.objects.filter(user_id__in=krisshaks + bhooswamis)
            except:
                return CalendarEvent.objects.none()

        return CalendarEvent.objects.filter(user=user)


    def perform_create(self, serializer):
        serializer.save(user=self.request.user, event_type='manual')


class CalendarEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.event_type == 'appointment':
            return Response({"error": "Appointment-linked events cannot be edited."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

