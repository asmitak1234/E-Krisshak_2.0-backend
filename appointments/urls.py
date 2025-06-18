from django.urls import path
from .views import AppointmentListCreateView, AppointmentRetrieveUpdateView, request_appointment, get_requests

urlpatterns = [
    path('', AppointmentListCreateView.as_view(), name='appointments'),
    path('<uuid:pk>/', AppointmentRetrieveUpdateView.as_view(), name='appointment-detail'),
    path('request/<int:bhooswami_id>/', request_appointment, name='request-appointment'),
    path('requests/', get_requests, name='get-requests'),
]
