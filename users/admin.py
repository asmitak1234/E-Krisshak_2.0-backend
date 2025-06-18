from django.contrib import admin
from appointments.models import Appointment
from contact.models import ContactMessage
from collections import Counter
from django.db.models import Avg, Count
from django.utils.html import format_html, format_html_join
from .models import CustomUser, KrisshakProfile, BhooswamiProfile, StateAdminProfile, DistrictAdminProfile, State, District, Rating, Favorite


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('name','user_type', 'email','unique_id', 'appointment_summary')
    
    inlines = []

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        if obj:
            if obj.user_type == 'krisshak':
                inline_instances.append(KrisshakAppointmentsInline(self.model, self.admin_site))
            if obj.user_type == 'bhooswami':
                inline_instances.append(BhooswamiAppointmentsInline(self.model, self.admin_site))
            inline_instances.append(SentContactMessageInline(self.model, self.admin_site))
        return inline_instances
    
    def appointment_summary(self, obj):
        if obj.user_type == 'bhooswami':
            related_appointments = Appointment.objects.filter(bhooswami=obj, status='confirmed')  # ✅ Filter only confirmed appointments
            counter = Counter(a.krisshak.email for a in related_appointments)
        elif obj.user_type == 'krisshak':
            related_appointments = Appointment.objects.filter(krisshak=obj, status='confirmed')  # ✅ Filter only confirmed appointments
            counter = Counter(a.bhooswami.email for a in related_appointments)
        else:
            return "N/A"

        total = sum(counter.values())

        lines = format_html_join(
            '<br>',
            '{} appointment{} with {}',
            [(count, '' if count == 1 else 's', name) for name, count in counter.items()]
        )

        return format_html(f"{lines}<br><strong>Total: {total}</strong>")


    appointment_summary.short_description = 'Appointments Info'

    def appointment_detail_view(self,obj):
        return self.appointment_summary(obj)
    
    appointment_detail_view.short_description = 'Detailed Appointments Info'

    readonly_fields=['unique_id','appointment_detail_view']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
class DistrictFilter(admin.SimpleListFilter):
    title = 'District'
    parameter_name = 'district'

    def lookups(self, request, model_admin):
        state_id = request.GET.get('state')
        if state_id:
            districts = District.objects.filter(state__id=state_id)
        else:
            districts = District.objects.all()
        return [(d.id, d.name) for d in districts]

    def queryset(self, request, queryset):
        district_id = self.value()
        if district_id:
            return queryset.filter(district__id=district_id)
        return queryset

class StateFilter(admin.SimpleListFilter):
    title = 'State'
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return [(s.id, s.name) for s in State.objects.all()]

    def queryset(self, request, queryset):
        state_id = self.value()
        if state_id:
            return queryset.filter(district__state__id=state_id)
        return queryset

class KrisshakAppointmentsInline(admin.TabularInline):
    model = Appointment
    fk_name = 'krisshak'
    extra = 0
    verbose_name_plural = "Confirmed Appointments"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='confirmed')  # ✅ Show only confirmed appointments

class BhooswamiAppointmentsInline(admin.TabularInline):
    model = Appointment
    fk_name = 'bhooswami'
    extra = 0
    verbose_name_plural = "Confirmed Appointments"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='confirmed')  # ✅ Show only confirmed appointments

    
class SentContactMessageInline(admin.TabularInline):
    model = ContactMessage
    fk_name = 'sender'
    extra = 0
    verbose_name_plural = "Messages Sent"
    fields = ('email', 'subject', 'message', 'created_at', 'forwarded_to')


@admin.register(KrisshakProfile)
class KrisshakProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_name', 'state', 'district')
    list_filter = [StateFilter, DistrictFilter]
    search_fields = ['user__email', 'get_name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser:
            return qs
        elif user.user_type == 'state_admin':
            try:
                return qs.filter(state=user.stateadminprofile.state)
            except StateAdminProfile.DoesNotExist:
                return qs.none()
        elif user.user_type == 'district_admin':
            try:
                return qs.filter(district=user.districtadminprofile.district)
            except DistrictAdminProfile.DoesNotExist:
                return qs.none()
        elif user.user_type == 'bhooswami':
            return qs.filter(appointment__status='confirmed')  # ✅ Filter only confirmed appointments
        else:
            return qs.filter(user=user)


    def get_name(self, obj):
        return obj.name
    get_name.short_description = 'Name'

    readonly_fields = ("ratings",)

@admin.register(BhooswamiProfile)
class BhooswamiProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_name', 'state', 'district')
    list_filter = [StateFilter, DistrictFilter]
    search_fields = ['user__email', 'get_name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser:
            return qs
        elif user.user_type == 'state_admin':
            try:
                return qs.filter(state=user.stateadminprofile.state)
            except StateAdminProfile.DoesNotExist:
                return qs.none()
        elif user.user_type == 'district_admin':
            try:
                return qs.filter(district=user.districtadminprofile.district)
            except DistrictAdminProfile.DoesNotExist:
                return qs.none()
        elif user.user_type == 'bhooswami':
            return qs.filter(appointment__status='confirmed')  # ✅ Filter only confirmed appointments
        else:
            return qs.filter(user=user)

    def get_name(self, obj):
        return obj.name
    get_name.short_description = 'Name'

    readonly_fields = ("ratings",)

@admin.register(StateAdminProfile)
class StateAdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_name', 'state', 'state_code')
    list_filter = [StateFilter]
    search_fields = ['state_name']

    def get_name(self, obj):
        return obj.state.name if obj.state else "-"
    get_name.short_description = 'Name'

@admin.register(DistrictAdminProfile)
class DistrictAdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_name', 'get_state', 'district', 'district_code')
    list_filter = [StateFilter, DistrictFilter]
    search_fields = ['district_name']

    def get_name(self, obj):
        return obj.district.name if obj.district else "-"

    get_name.short_description = 'Name'

    def get_state(self, obj):
        return obj.district.state.name if obj.district and obj.district.state else "-"
    get_state.short_description = 'State'

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'state')
    list_filter = ['state']
    search_fields = ['name']

class RatingAdmin(admin.ModelAdmin):
    list_display = ("rater", "rated_user_email", "rating_value","average_rating", "rating_count", "created_at")
    search_fields = ("rater__email", "rated_user__email")

    # ordering = ["-average_rating"]

    def get_queryset(self, request):
        qs = (
            super().get_queryset(request)
            .select_related("rater", "rated_user")
            .annotate(
                average_rating=Avg("rated_user__received_ratings__rating_value"),
                rating_count=Count("rated_user__received_ratings")
            )
        )
        return qs

    def rated_user_email(self, obj):
        return obj.rated_user.email

    def average_rating(self, obj):
        return round(obj.average_rating, 1)

    def rating_count(self, obj):
        return obj.rating_count

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["favorited_user", "favourite_count","user", "krisshak", "bhooswami", "created_at"]
    search_fields = ["user__email"]
    # ordering = ["-favourite_count"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("krisshak__user", "bhooswami__user")
            .annotate(favourite_count=Count("id"))
        )


    def favorited_user(self, obj):
        if obj.krisshak:
            return obj.krisshak.user.email
        elif obj.bhooswami:
            return obj.bhooswami.user.email
        return None


    def favourite_count(self, obj):
        return obj["favourite_count"]

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Rating,RatingAdmin)

