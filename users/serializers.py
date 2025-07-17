from rest_framework import serializers
from .models import CustomUser, KrisshakProfile, BhooswamiProfile, StateAdminProfile, DistrictAdminProfile, Favorite, District, State
from appointments.serializers import AppointmentSerializer
from appointments.models import Appointment
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = "__all__" 

    def get_profile_picture(self, obj): 
        request = self.context.get("request") 
        return obj.get_profile_picture(request=request)
        
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name']

        
class RegisterSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False)

    # Accept IDs on write
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), write_only=True, required=False)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), write_only=True, required=False)

    # Show names on read
    state_name = serializers.SerializerMethodField(read_only=True)
    district_name = serializers.SerializerMethodField(read_only=True)
   
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'user_type','name','age','gender','phone_number','preferred_language','profile_picture','state','district','state_name','district_name']
        extra_kwargs = {'password': {'write_only': True}}

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return obj.get_profile_picture(request=request)
    
    def get_state_name(self, obj):
        try:
            if obj.user_type == "krisshak" and hasattr(obj, "krisshakprofile"):
                return obj.krisshakprofile.state.name
            elif obj.user_type == "bhooswami" and hasattr(obj, "bhooswamiprofile"):
                return obj.bhooswamiprofile.state.name
            elif obj.user_type == "district_admin" and hasattr(obj, "districtadminprofile"):
                return obj.districtadminprofile.district.state.name
            elif obj.user_type == "state_admin" and hasattr(obj, "stateadminprofile"):
                return obj.stateadminprofile.state.name
        except:
            pass
        return None

    def get_district_name(self, obj):
        try:
            if obj.user_type == "krisshak" and hasattr(obj, "krisshakprofile"):
                return obj.krisshakprofile.district.name
            elif obj.user_type == "bhooswami" and hasattr(obj, "bhooswamiprofile"):
                return obj.bhooswamiprofile.district.name
            elif obj.user_type == "district_admin" and hasattr(obj, "districtadminprofile"):
                return obj.districtadminprofile.district.name
        except:
            pass
        return None

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        
        user = self.context.get("request").user
        if CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value

    def create(self, validated_data):
        state = validated_data.pop("state", None)
        district = validated_data.pop("district", None)

        user = CustomUser(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        if user.user_type == "krisshak":
            KrisshakProfile.objects.create(user=user, state=state, district=district)
        elif user.user_type == "bhooswami":
            BhooswamiProfile.objects.create(user=user, state=state, district=district)
        elif user.user_type == "state_admin":
            StateAdminProfile.objects.create(user=user, state=state)
        elif user.user_type == "district_admin":
            DistrictAdminProfile.objects.create(user=user, district=district)

        return user


class KrisshakProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    appointment = serializers.SerializerMethodField()

    class Meta:
        model = KrisshakProfile
        fields = "__all__"

    def validate(self, attrs):
        if not attrs.get("account_number") and not attrs.get("upi_id"):
            raise serializers.ValidationError("Krisshaks must provide either a bank account number or UPI ID for payouts.")
        return attrs

    def get_appointment(self, obj):
        request = self.context.get("request")
        logged_in_user = request.user

        try:
            appointment = Appointment.objects.filter(
                status="confirmed",
                sender_user__in=[logged_in_user, obj.user],
                recipient_user__in=[logged_in_user, obj.user]
            ).latest("created_at")
            return AppointmentSerializer(appointment).data
        except Appointment.DoesNotExist:
            return None

class BhooswamiProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    appointment = serializers.SerializerMethodField()
    
    class Meta:
        model = BhooswamiProfile
        fields = "__all__"

    def get_appointment(self, obj):
        request = self.context.get("request")
        logged_in_user = request.user

        try:
            appointment = Appointment.objects.filter(
                status="confirmed",
                sender_user__in=[logged_in_user, obj.user],
                recipient_user__in=[logged_in_user, obj.user]
            ).latest("created_at")
            return AppointmentSerializer(appointment).data
        except Appointment.DoesNotExist:
            return None

class StateAdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateAdminProfile
        exclude = ['user', 'state_code']  # state_code not editable

class DistrictAdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistrictAdminProfile
        exclude = ['user', 'district_code']


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["krisshak", "bhooswami", "created_at"]
