from django.http import JsonResponse
from django.db.models import Q
from users.models import KrisshakProfile, BhooswamiProfile, CustomUser, StateAdminProfile, DistrictAdminProfile
from appointments.models import Appointment
from .utils import get_current_season, get_favorable_crops, get_ai_crop_recommendations
from search.ml_recommendation import get_krisshak_recommendations, get_bhooswami_recommendations
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

# 🔍 Seasonal Crop Suggestions
def seasonal_crop_suggestions(request):
    """Returns crop recommendations based on the current season."""
    season = get_current_season()
    seasonal_crops = get_favorable_crops(season)
    
    return JsonResponse({"season": season, "seasonal_crops": seasonal_crops}, safe=False)

# 🔍 AI-Based Crop Suggestions
def ai_crop_suggestions(request):
    """Returns AI-powered crop suggestions based on soil nutrients."""
    soil_ph = request.GET.get("soil_ph")
    nitrogen = request.GET.get("nitrogen")
    phosphorus = request.GET.get("phosphorus")
    potassium = request.GET.get("potassium")

    ai_crops = []
    if soil_ph and nitrogen and phosphorus and potassium:
        ai_crops = get_ai_crop_recommendations(float(soil_ph), float(nitrogen), float(phosphorus), float(potassium))

    return JsonResponse({"ai_crops": ai_crops}, safe=False)

# 🔍 Smart Suggestions (ML + Seasonal + AI-Based)
def get_smart_suggestions(request):
    """Suggests Krisshaks & Bhooswamis based on previous appointments, seasonal crops, and AI recommendations."""
    user = request.user
    season = get_current_season()
    seasonal_crops = get_favorable_crops(season)

    soil_ph = request.GET.get("soil_ph")
    nitrogen = request.GET.get("nitrogen")
    phosphorus = request.GET.get("phosphorus")
    potassium = request.GET.get("potassium")

    # Fetch Krisshaks previously appointed by the Bhooswami
    previous_appointments = KrisshakProfile.objects.filter(
        user__in=Appointment.objects.filter(bhooswami=user, status="confirmed").values_list("krisshak_id", flat=True)
    )

    # Suggest Krisshaks specializing in seasonal crops
    seasonal_suggestions = KrisshakProfile.objects.filter(
        Q(specialization__icontains=seasonal_crops[0]) | Q(specialization__icontains=seasonal_crops[1])
    ).order_by("-ratings", "-availability")

    # Suggest Krisshaks based on AI-suggested crops (if provided)
    ai_suggestions = []
    if soil_ph and nitrogen and phosphorus and potassium:
        ai_crops = get_ai_crop_recommendations(float(soil_ph), float(nitrogen), float(phosphorus), float(potassium))
        ai_suggestions = KrisshakProfile.objects.filter(
            Q(specialization__icontains=ai_crops[0]) | Q(specialization__icontains=ai_crops[1])
        ).order_by("-ratings", "-availability")

    # 🔍 Include Krisshaks that match Bhooswami's required crops
    required_crops_suggestions = KrisshakProfile.objects.filter(
        Q(specialization__icontains=user.bhooswamiprofile.requirements)
    ).order_by("-ratings", "-availability")

    # Merge lists in priority order
    final_suggestions = list(previous_appointments) + list(seasonal_suggestions) + list(ai_suggestions) + list(required_crops_suggestions)

    return JsonResponse({
        "previous_appointments": [krisshak.to_dict() for krisshak in previous_appointments] if previous_appointments else [],
        "seasonal_suggestions": [krisshak.to_dict() for krisshak in seasonal_suggestions] if seasonal_suggestions else [],
        "ai_suggestions": [krisshak.to_dict() for krisshak in ai_suggestions] if ai_suggestions else [],
        "required_crops_suggestions": [krisshak.to_dict() for krisshak in required_crops_suggestions] if required_crops_suggestions else [],
        "final_suggestions": [krisshak.to_dict() for krisshak in final_suggestions] if final_suggestions else [],
    }, safe=False)

# ✅ Krisshak Search (with ML Recommendations)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def search_krisshaks(request):
    """Suggest Krisshaks for Bhooswamis based on previous hiring & crop requirements."""

    if not request.user or not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    user = request.user

    # 👇 Add this block immediately after setting `user`
    from django.contrib.auth import get_user_model
    CustomUser = get_user_model()
    if isinstance(user, str):
        try:
            user = CustomUser.objects.get(email=user)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "Invalid user reference."}, status=400)

    try:
        print("🧠 user =", user, "| type:", type(user))
        bhooswami_profile = BhooswamiProfile.objects.get(user=user)
    except BhooswamiProfile.DoesNotExist:
        return JsonResponse({"error": "Bhooswami profile not found"}, status=404)

    # ...rest of your logic

    required_crops = bhooswami_profile.requirements  # Fetch crop requirements

    # Fetch previously hired Krisshaks
    previous_krisshaks = KrisshakProfile.objects.filter(
        user__in=Appointment.objects.filter(bhooswami=user, status='confirmed').values_list('krisshak__id', flat=True),
        district=bhooswami_profile.district  # ✅ Restrict search to user's district
    )

    # Suggest Krisshaks whose specialization matches Bhooswami’s crop requirements
    matching_krisshaks = KrisshakProfile.objects.filter(
        Q(specialization__icontains=required_crops)
    ).order_by('-ratings')

    ml_suggestions = get_krisshak_recommendations(bhooswami_profile)

    final_suggestions = list(previous_krisshaks) + list(matching_krisshaks) + list(ml_suggestions)

    return JsonResponse({
        "previous_krisshaks": [krisshak.to_dict() for krisshak in previous_krisshaks] if previous_krisshaks else [],
        "matching_krisshaks": [krisshak.to_dict() for krisshak in matching_krisshaks] if matching_krisshaks else [],
        "ml_suggestions": [krisshak.to_dict() for krisshak in ml_suggestions] if ml_suggestions else [],
        "final_suggestions": [krisshak.to_dict() for krisshak in final_suggestions] if final_suggestions else [],
    }, safe=False)

# ✅ Bhooswami Search (with ML Recommendations)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def search_bhooswamis(request):
    """Suggest Bhooswamis for Krisshaks based on previous hiring & specialization."""
    user = request.user
    specialization = request.GET.get("specialization")  # Krisshak’s expertise

    # Fetch Bhooswamis who previously appointed the Krisshak
    previous_bhooswamis = BhooswamiProfile.objects.filter(
        user__in=Appointment.objects.filter(krisshak=user, status='confirmed').values_list('bhooswami_id', flat=True),
        district=user.krisshakprofile.district  # ✅ Restrict search to user's district
    )

    # Suggest Bhooswamis whose requirements match Krisshak’s specialization
    matching_bhooswamis = BhooswamiProfile.objects.filter(
        Q(requirements__icontains=specialization)
    ).order_by('-ratings')

    ml_suggestions = get_bhooswami_recommendations(user)

    final_suggestions = list(previous_bhooswamis) + list(matching_bhooswamis) + list(ml_suggestions)

    return JsonResponse({
        "previous_bhooswamis": [bhooswami.to_dict() for bhooswami in previous_bhooswamis] if previous_bhooswamis else [],
        "matching_bhooswamis": [bhooswami.to_dict() for bhooswami in matching_bhooswamis] if matching_bhooswamis else [],
        "ml_suggestions": [bhooswami.to_dict() for bhooswami in ml_suggestions] if ml_suggestions else [],
        "final_suggestions": [bhooswami.to_dict() for bhooswami in final_suggestions] if final_suggestions else [],
    }, safe=False)


# ✅ Filtering Users by District, Age, Specialization, Availability
def get_filtered_users(request):
    """Allows admins & users to filter Krisshaks/Bhooswamis based on district & other properties."""
    user = request.user
    district_id = request.GET.get("district_id")  # Filter by district
    age = request.GET.get("age")
    specialization = request.GET.get("specialization")
    availability = request.GET.get("availability")  # Filter by availability
    user_type = request.GET.get("user_type")  # Krisshak or Bhooswami

    # Base query: restrict results based on user type
    if user.user_type == 'krisshak':
        queryset = BhooswamiProfile.objects.filter(district=user.krisshakprofile.district)
    elif user.user_type == 'bhooswami':
        queryset = KrisshakProfile.objects.filter(district=user.bhooswamiprofile.district)
    elif user.user_type == 'district_admin':
        try:
            queryset = CustomUser.objects.filter(district=user.districtadminprofile.district)
        except DistrictAdminProfile.DoesNotExist:
            return JsonResponse({"error": "District not found"}, status=404)
    elif user.user_type == 'state_admin':
        try:
            queryset = CustomUser.objects.filter(district__state=user.stateadminprofile.state)
        except StateAdminProfile.DoesNotExist:
            return JsonResponse({"error": "State not found"}, status=404)
    else:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Apply filters dynamically
    if district_id:
        queryset = queryset.filter(district_id=district_id)

    if age:
        queryset = queryset.filter(age=int(age))

    if specialization:
        queryset = queryset.filter(Q(specialization__icontains=specialization))

    if availability:
        queryset = queryset.filter(availability=True)  # ✅ Only show available users

    # Sorting results
    queryset = queryset.order_by("-availability", "-ratings")  # ✅ Ensures available users appear first

    return JsonResponse({"filtered_users": [user.to_dict() for user in queryset]}, safe=False)
