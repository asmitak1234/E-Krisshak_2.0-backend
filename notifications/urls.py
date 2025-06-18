from django.urls import path
from .views import NotificationListView, MarkNotificationReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('read/<int:pk>/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
]
