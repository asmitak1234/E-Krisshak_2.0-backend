from django.contrib import admin
from .models import Appointment, AppointmentRequest

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'bhooswami', 'krisshak', 'date', 'time', 'status', 'payment_status', 'get_state', 'get_district')

    ordering = (
        'krisshak__krisshakprofile__state__name',
        'krisshak__krisshakprofile__district__name',
        'date',
    )

    list_filter = (
        'status', 'payment_status', 'date',
        ('krisshak__krisshakprofile__state', admin.RelatedOnlyFieldListFilter),
        ('krisshak__krisshakprofile__district', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('bhooswami__email', 'krisshak__email')

    def get_state(self, obj):
        try:
            return obj.krisshak.krisshakprofile.state.name
        except:
            return '-'
    get_state.short_description = 'State'

    def get_district(self, obj):
        try:
            return obj.krisshak.krisshakprofile.district.name
        except:
            return '-'
    get_district.short_description = 'District'

class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'krisshak', 'bhooswami', 'status', 'request_time')
    ordering = ('-request_time',)
    list_filter = ('status',)
    search_fields = ('krisshak__email', 'bhooswami__email')

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(AppointmentRequest, AppointmentRequestAdmin)
