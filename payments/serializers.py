from rest_framework import serializers
from .models import Payment

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['recipient', 'amount', 'purpose', 'type']

class PaymentListSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.email', read_only=True)
    recipient_name = serializers.CharField(source='recipient.email', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'type', 'status', 'purpose', 'created_at', 'sender_name', 'recipient_name']
