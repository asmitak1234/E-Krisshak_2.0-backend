from rest_framework import serializers
from .models import ContactMessage, Notice

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = [
            'sender', 'state', 'district', 'forwarded_to',
            'is_admin_reply', 'is_resolved', 'parent'
        ]


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ["author_name", "content", "timestamp"]
