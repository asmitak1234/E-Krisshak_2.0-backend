from django.urls import path
from .views import ContactMessageView, ContactMessageListView, ContactReplyView, get_notices, create_notice

urlpatterns = [
    path('send/', ContactMessageView.as_view(), name='send-contact-message'),
    path('inbox/', ContactMessageListView.as_view(), name='view-contact-messages'),
    path('reply/<int:pk>/', ContactReplyView.as_view(), name='reply-contact-message'),
    path("notices/", get_notices, name="get_notices"),
    path("notices/create/", create_notice, name="create_notice"),
]
