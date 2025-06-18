from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'amount', 'type', 'status', 'created_at')
    list_filter = ('status', 'type', 'created_at')
    search_fields = ('sender__email', 'recipient__email', 'purpose', 'external_payment_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'external_payment_id')
