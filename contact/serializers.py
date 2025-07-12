from rest_framework import serializers
from .models import ContactMessage, Notice

class ContactMessageSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = [
            'sender', 'state', 'district', 'forwarded_to',
            'is_admin_reply', 'is_resolved', 'parent'
        ]

    def get_replies(self, obj):
        children = obj.replies.order_by("created_at")
        return ContactMessageSerializer(children, many=True).data

    def validate_email(self, value):
        if not value or "@" not in value:
            raise serializers.ValidationError("Provide a valid email.")
        return value

    def validate_message(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Message too short.")
        return value


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ["author_name", "content", "timestamp"]
