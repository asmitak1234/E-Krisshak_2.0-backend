import random, string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics,permissions,serializers
from .models import CustomUser,KrisshakProfile,BhooswamiProfile,StateAdminProfile,DistrictAdminProfile,Rating, Favorite, District, State
from .serializers import RegisterSerializer, KrisshakProfileSerializer,BhooswamiProfileSerializer, FavoriteSerializer, DistrictSerializer, StateSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
import json 
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
import traceback
from django.conf import settings

class StateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        states = State.objects.all().order_by("name")
        serializer = StateSerializer(states, many=True)
        return Response(serializer.data)

@permission_classes([AllowAny])
class DistrictsByStateView(APIView):
    def get(self, request):
        state_id = request.GET.get("state_id")
        if not state_id:
            return Response({"error": "state_id is required"}, status=400)

        districts = District.objects.filter(state_id=state_id).order_by('name')
        serializer = DistrictSerializer(districts, many=True)
        return Response(serializer.data)
    
    
class UserRoleAccessPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True

        if hasattr(obj, 'user'):
            obj_user = obj.user
        else:
            obj_user = obj

        if obj_user == user:
            return True

        if user.user_type == 'state_admin':
            try:
                state_admin = user.stateadminprofile
                return hasattr(obj, 'state') and obj.state == state_admin.state
            except StateAdminProfile.DoesNotExist:
                return False

        if user.user_type == 'district_admin':
            try:
                district_admin = user.districtadminprofile
                return hasattr(obj, 'district') and obj.district == district_admin.district
            except DistrictAdminProfile.DoesNotExist:
                return False

        return False

class RoleBasedLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        role = request.data.get('role')
        username_or_email = request.data.get('username_or_email')
        password = request.data.get('password')
        preferred_language = request.data.get('preferred_language', 'en')  # Default to English

        if not role or not username_or_email or not password:
            return Response({"error": "Role, username/email, and password are required."}, status=400)

        user = authenticate(username=username_or_email, password=password)

        if user is None:
            return Response({"error": "Invalid credentials."}, status=401)

        if user.user_type != role:
            return Response({"error": "Selected role does not match the user type."}, status=403)

        if not user.is_active:
            return Response({"error": "User account is inactive."}, status=403)

        user.preferred_language = preferred_language  # Update preferred language upon login
        user.save()

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "message": f"{role.capitalize()} login successful.",
            "token": token.key,
            "preferred_language": user.preferred_language, # Return user's selected language
            "user_id": user.id
        })

class FilteredKrisshakListView(generics.ListAPIView):
    serializer_class = KrisshakProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}
    
    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return KrisshakProfile.objects.all()

        if user.user_type == 'state_admin':
            try:
                state = user.stateadminprofile.state
                return KrisshakProfile.objects.filter(state=state).order_by('-availability')
            except:
                return KrisshakProfile.objects.none()

        if user.user_type == 'district_admin':
            try:
                district = user.districtadminprofile.district
                return KrisshakProfile.objects.filter(district=district).order_by('-availability')
            except:
                return KrisshakProfile.objects.none()

        return KrisshakProfile.objects.filter(user=user).order_by('-availability')

class FilteredBhooswamiListView(generics.ListAPIView):
    serializer_class = BhooswamiProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_context(self):
        return {"request": self.request}
    
    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return BhooswamiProfile.objects.all()

        if user.user_type == 'state_admin':
            try:
                state = user.stateadminprofile.state
                return BhooswamiProfile.objects.filter(state=state)
            except:
                return BhooswamiProfile.objects.none()

        if user.user_type == 'district_admin':
            try:
                district = user.districtadminprofile.district
                return BhooswamiProfile.objects.filter(district=district)
            except:
                return BhooswamiProfile.objects.none()

        return BhooswamiProfile.objects.filter(user=user)

# ✅ View any Krisshak profile by ID (for Appointments, Search, etc.)
class KrisshakPublicDetailView(generics.RetrieveAPIView):
    serializer_class = KrisshakProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(KrisshakProfile, user__id=self.kwargs["pk"])
    
    def get_serializer_context(self):
        return {"request": self.request}
    
# ✅ Update your own Krisshak profile
class KrisshakProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = KrisshakProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return KrisshakProfile.objects.get(user=self.request.user)

    def perform_update(self, serializer):
        account_number = serializer.validated_data.get("account_number")
        upi_id = serializer.validated_data.get("upi_id")

        if not account_number and not upi_id:
            raise serializers.ValidationError(
                "Krisshaks must provide either a bank account number or UPI ID for payouts."
            )
        serializer.save()

# ✅ View any Bhooswami profile by ID
class BhooswamiDetailView(generics.RetrieveAPIView):
    
    serializer_class = BhooswamiProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(BhooswamiProfile, user__id=self.kwargs["pk"])
    
    def get_serializer_context(self):
        return {"request": self.request}
    
# ✅ Update your own Bhooswami profile
class BhooswamiProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = BhooswamiProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return BhooswamiProfile.objects.get(user=self.request.user)


class RegisterView(APIView):

    permission_classes = [AllowAny] 
    
    def post(self, request):
        print("🔥 Step 1: Incoming data:", request.data)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                try:
                    user = serializer.save()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print("🚨 Error in serializer.save():", str(e))
                    return JsonResponse({"error": "Could not save user", "detail": str(e)}, status=500)
 
                print("✅ Step 2: User saved:", user.email)

                otp = ''.join(random.choices(string.digits, k=6))
                user.otp_code = otp
                user.otp_expiry = timezone.now() + timedelta(minutes=10)
                user.save()
                print("✅ Step 3: OTP set and saved")

                try:
                    result = send_mail(
                        subject="Verify Your Email (Ekrisshak 2.0)",
                        message=f"Your OTP is: {otp}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email]
                    )
                    print("✅ Step 4: Email sent successfully:", result)
                except Exception as email_error:
                    print("📭 Step 4: Email sending failed:", str(email_error))
                    return Response({"error": "User created, but failed to send OTP email."}, status=202)

                return Response({"message": "User created and OTP sent!"}, status=201)

            except Exception as e:
                traceback.print_exc() 
                print("🚨 Step X: Exception after serializer.valid():", str(e))
                return JsonResponse({"error": "Fatal error after user creation", "detail": str(e)}, status=500)

        else:
            print("❌ Step 0: Validation errors:", serializer.errors)
            return Response(serializer.errors, status=400)

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        try:
            user = CustomUser.objects.get(email=email)
            if user.otp_code == otp and timezone.now() <= user.otp_expiry:
                user.is_email_verified = True
                user.otp_code = None
                user.otp_expiry = None
                user.save()
                return Response({"message": "Email verified successfully."})
            return Response({"error": "Invalid or expired OTP."}, status=400)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = ''.join(random.choices(string.digits, k=6))
            user.otp_code = otp
            user.otp_expiry = timezone.now() + timedelta(minutes=10)
            user.save()
            send_mail(
                subject="Reset Password - Ekrisshak 2.0",
                message=f"Your password reset OTP is: {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email]
            )
            return Response({"message": "OTP sent to email."})
        except CustomUser.DoesNotExist:
            return Response({"error": "Email not found."}, status=404)

class ResetPasswordView(APIView):
    """
    Handles:
    - Authenticated users: no OTP needed; just supply new_password (in profile)
    - Unauthenticated users (via email): needs OTP and email
    """
    permission_classes = [AllowAny]  # We’ll check inside manually

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        data = request.data

        new_password = data.get('new_password')

        if request.user.is_authenticated:
            otp = data.get("otp")
            if not new_password or not otp:
                return Response({"error": "New password and OTP required."}, status=400)

            try:
                user = CustomUser.objects.get(id=request.user.id)
            except CustomUser.DoesNotExist:
                return Response({"error": "Authenticated user not found."}, status=404)

            if user.otp_code != otp or timezone.now() > user.otp_expiry:
                return Response({"error": "Invalid or expired OTP."}, status=400)

            user.set_password(new_password)
            user.otp_code = None
            user.otp_expiry = None
            user.save()
            return Response({"message": "Password updated successfully."})

        else:
            # Public reset via email + OTP
            email = data.get("email")
            otp = data.get("otp")

            if not email or not otp or not new_password:
                return Response({"error": "Email, OTP, and new password are required."}, status=400)

            try:
                user = CustomUser.objects.get(email=email)

                # Block admins from using public reset
                if user.user_type in ["state_admin", "district_admin"]:
                    return Response({"error": "Password reset not allowed for this role."}, status=403)

                if user.otp_code == otp and timezone.now() <= user.otp_expiry:
                    user.set_password(new_password)
                    user.otp_code = None
                    user.otp_expiry = None
                    user.save()
                    return Response({"message": "Password reset successfully."})
                return Response({"error": "Invalid or expired OTP."}, status=400)

            except CustomUser.DoesNotExist:
                return Response({"error": "User not found."}, status=404)
      

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
    

class UpdateProfileView(generics.RetrieveUpdateAPIView):
    """Allow users to update their profile, including gender & profile picture"""
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user
    
    def get_serializer_context(self):
        return {"request": self.request}
    
   
    def perform_update(self, serializer):
        try:
            user = serializer.save()
            print("✅ Image uploaded:", user.profile_picture.path)
            print("✅ Saved image:", user.profile_picture.url)
        except Exception as e:
            print("🚨 Error saving profile update:", str(e))
            raise

  
@csrf_exempt
def rate_user(request):
    """Allows users to rate Krisshaks or Bhooswamis."""
    try:
        data = json.loads(request.body)
        rater = request.user
        rated_user_id = data.get("rated_user_id")
        rating_value = float(data.get("rating"))

        if not (1.0 <= rating_value <= 5.0):
            return JsonResponse({"error": "Invalid rating value"}, status=400)

        rated_user = CustomUser.objects.get(id=rated_user_id)

        # Create or update the rating
        rating, created = Rating.objects.update_or_create(
            rater=rater, rated_user=rated_user, defaults={"rating_value": rating_value}
        )

        # Recalculate the average rating for the rated user
        if KrisshakProfile.objects.filter(user=rated_user).exists():
            krisshak = KrisshakProfile.objects.get(user=rated_user)
            krisshak.calculate_average_rating()
        elif BhooswamiProfile.objects.filter(user=rated_user).exists():
            bhooswami = BhooswamiProfile.objects.get(user=rated_user)
            bhooswami.calculate_average_rating()

        return JsonResponse({"message": "Rating updated successfully", "new_rating": rating_value})
    
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def rated_users_view(request):
    user = request.user
    rated_ids = Rating.objects.filter(rater=user).values_list("rated_user_id", flat=True)
    return JsonResponse({"rated_user_ids": list(rated_ids)})


@api_view(["POST"])
def toggle_favorite(request):
    """Toggle favorite status for a Krisshak or Bhooswami."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    krisshak_id = request.data.get("krisshak_id")
    bhooswami_id = request.data.get("bhooswami_id")

    if user.user_type == "krisshak" and bhooswami_id:  # ✅ Krisshaks can only favorite Bhooswamis
        bhooswami = BhooswamiProfile.objects.get(id=bhooswami_id, district=user.krisshakprofile.district)
        favorite, created = Favorite.objects.get_or_create(user=user, bhooswami=bhooswami)
        if not created:  # If already favorited, remove it
            favorite.delete()
            return JsonResponse({"message": "Favorite removed"}, status=200)
        return JsonResponse({"message": "Favorite added"}, status=201)

    if user.user_type == "bhooswami" and krisshak_id:  # ✅ Bhooswamis can only favorite Krisshaks
        krisshak = KrisshakProfile.objects.get(id=krisshak_id, district=user.bhooswamiprofile.district)
        favorite, created = Favorite.objects.get_or_create(user=user, krisshak=krisshak)
        if not created:  # If already favorited, remove it
            favorite.delete()
            return JsonResponse({"message": "Favorite removed"}, status=200)
        return JsonResponse({"message": "Favorite added"}, status=201)

    return JsonResponse({"error": "Invalid request"}, status=400)

@api_view(["GET"])
def get_favorites(request):
    """Retrieve user's favorite Krisshaks & Bhooswamis."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    favorites = Favorite.objects.filter(user=user)
    serialized_favorites = FavoriteSerializer(favorites, many=True).data

    return JsonResponse({"favorites": serialized_favorites}, safe=False)
