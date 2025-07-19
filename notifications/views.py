from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
            notif.is_read = True
            notif.save()
            return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

def get_unread_count(request):
    """Fetch count of unread notifications for each category."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    categories = ["notice", "requests", "calender", "contact"]
    unread_counts = {category: Notification.objects.filter(recipient=user, notification_type=category, is_read=False).count() for category in categories}

    return JsonResponse({"unread_counts": unread_counts}, safe=False)

def mark_as_read(request, category):
    """Mark all notifications in a category as read."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    Notification.objects.filter(recipient=user, notification_type=category).update(is_read=True)

    return JsonResponse({"message": f"Marked {category} notifications as read."}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_subscription(request):
    request.user.push_subscription = request.data.get("subscription")
    request.user.save()
    return Response({"status": "saved", "subscription": request.user.push_subscription})