from django.urls import path
from .views import AppointmentListCreateView, AppointmentRetrieveUpdateView, request_appointment, get_requests, accept_request, cancel_request

urlpatterns = [
    path('', AppointmentListCreateView.as_view(), name='appointments'),
    path('<uuid:pk>/', AppointmentRetrieveUpdateView.as_view(), name='appointment-detail'),
    path('request/<int:user_id>/', request_appointment, name='send-request'),
    path('requests/', get_requests, name='get-requests'),
    path('accept-request/<int:request_id>/', accept_request, name='accept-request'),
    path('cancel-request/<int:request_id>/', cancel_request, name='cancel-request'),

]
