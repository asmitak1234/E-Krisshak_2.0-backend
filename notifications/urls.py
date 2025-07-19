from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, save_subscription

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('read/<int:pk>/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
    path("save-subscription/", save_subscription),
]
