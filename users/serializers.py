from rest_framework import serializers
from .models import CustomUser, KrisshakProfile, BhooswamiProfile, StateAdminProfile, DistrictAdminProfile, Favorite, District, State
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name']

        
class RegisterSerializer(serializers.ModelSerializer):
    permission_classes = [AllowAny]

    def post(self, request):
        print("🚀 Incoming registration data:", request.data)  # Add this

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."})
        else:
            print("❌ Validation errors:", serializer.errors)  # Add this
            return Response(serializer.errors, status=400)
        
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'user_type','name','age','gender','phone_number','preferred_language','profile_picture']
        extra_kwargs = {'password': {'write_only': True}}

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
        user = CustomUser(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class KrisshakProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = KrisshakProfile
        fields = '__all__'

class BhooswamiProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BhooswamiProfile
        fields = '__all__'

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
