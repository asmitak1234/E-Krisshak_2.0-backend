from rest_framework import serializers
from .models import CustomUser, KrisshakProfile, BhooswamiProfile, StateAdminProfile, DistrictAdminProfile, Favorite, District, State

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
    profile_picture = serializers.SerializerMethodField()
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), write_only=True, required=False)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'user_type','name','age','gender','phone_number','preferred_language','profile_picture','state','district']
        extra_kwargs = {'password': {'write_only': True}}

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return obj.get_profile_picture(request=request)
    
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        if CustomUser.objects.filter(email=value).exists():
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
    
    class Meta:
        model = KrisshakProfile
        fields = "__all__"

class BhooswamiProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BhooswamiProfile
        fields = "__all__"

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
