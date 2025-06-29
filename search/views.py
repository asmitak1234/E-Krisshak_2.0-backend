from django.http import JsonResponse
from django.db.models import Q
from users.models import KrisshakProfile, BhooswamiProfile, CustomUser, StateAdminProfile, DistrictAdminProfile
from appointments.models import Appointment
from .utils import get_current_season, get_favorable_crops, get_ai_crop_recommendations
from search.ml_recommendation import get_krisshak_recommendations, get_bhooswami_recommendations
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from itertools import chain

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
        "previous_appointments": [krisshak.to_dict(request) for krisshak in previous_appointments] if previous_appointments else [],
        "seasonal_suggestions": [krisshak.to_dict(request) for krisshak in seasonal_suggestions] if seasonal_suggestions else [],
        "ai_suggestions": [krisshak.to_dict(request) for krisshak in ai_suggestions] if ai_suggestions else [],
        "required_crops_suggestions": [krisshak.to_dict(request) for krisshak in required_crops_suggestions] if required_crops_suggestions else [],
        "final_suggestions": [krisshak.to_dict(request) for krisshak in final_suggestions] if final_suggestions else [],
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

    

    seen = set()
    final_suggestions = []
    for k in chain(previous_krisshaks, matching_krisshaks, ml_suggestions):
        if k.user.id not in seen:  # assuming user.id is unique per profile
            seen.add(k.user.id)
            final_suggestions.append(k)

    return JsonResponse({
        "previous_krisshaks": [krisshak.to_dict(request) for krisshak in previous_krisshaks] if previous_krisshaks else [],
        "matching_krisshaks": [krisshak.to_dict(request) for krisshak in matching_krisshaks] if matching_krisshaks else [],
        "ml_suggestions": [krisshak.to_dict(request) for krisshak in ml_suggestions] if ml_suggestions else [],
        "final_suggestions": [krisshak.to_dict(request) for krisshak in final_suggestions] if final_suggestions else [],
    }, safe=False)

# ✅ Bhooswami Search (with ML Recommendations)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def search_bhooswamis(request):
    """Suggest Bhooswamis for Krisshaks based on previous hiring & specialization."""

    if not request.user or not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    user = request.user

    # Align with your krisshak view: fallback if user is a string
    CustomUser = get_user_model()
    if isinstance(user, str):
        try:
            user = CustomUser.objects.get(email=user)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "Invalid user reference."}, status=400)

    # Ensure krisshak profile exists
    try:
        krisshak_profile = KrisshakProfile.objects.get(user=user)
    except KrisshakProfile.DoesNotExist:
        return JsonResponse({"error": "Krisshak profile not found"}, status=404)

    specialization = krisshak_profile.specialization  # fallback if not in request
    if not specialization:
        specialization = request.GET.get("specialization") or ""

    # Fetch Bhooswamis who previously appointed this Krisshak
    previous_bhooswamis = BhooswamiProfile.objects.filter(
        user__in=Appointment.objects.filter(krisshak=user, status='confirmed')
                                     .values_list('bhooswami_id', flat=True),
        district=krisshak_profile.district
    )

    # Recommend based on matching requirements
    matching_bhooswamis = BhooswamiProfile.objects.filter(
        Q(requirements__icontains=specialization),
        district=krisshak_profile.district
    ).order_by("-ratings")

    ml_suggestions = get_bhooswami_recommendations(krisshak_profile)

    # Combine and dedupe
    seen = set()
    final_suggestions = []
    for b in chain(previous_bhooswamis, matching_bhooswamis, ml_suggestions):
        if b.user.id not in seen:
            seen.add(b.user.id)
            final_suggestions.append(b)

    return JsonResponse({
        "previous_bhooswamis": [b.to_dict(request) for b in previous_bhooswamis],
        "matching_bhooswamis": [b.to_dict(request) for b in matching_bhooswamis],
        "ml_suggestions": [b.to_dict(request) for b in ml_suggestions],
        "final_suggestions": [b.to_dict(request) for b in final_suggestions],
    }, safe=False)

# ✅ Filtering Users by District, Age, Specialization, Availability and other parameters

def model_has_field(model, field_name):
    return field_name in [f.name for f in model._meta.get_fields()]

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_filtered_users(request):
    """Allows admins & users to filter Krisshaks/Bhooswamis based on district & other properties."""

    user = request.user
    if not user or not user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Text filters (partial match)
    specialization = request.GET.get("specialization")
    requirements = request.GET.get("requirements")
    land_location = request.GET.get("land_location")

    # Number filters (with operator support)
    age_min = request.GET.get("age_min")
    age_max = request.GET.get("age_max")
    experience_min = request.GET.get("experience_min")
    experience_max = request.GET.get("experience_max")
    land_area_min = request.GET.get("land_area_min")
    land_area_max = request.GET.get("land_area_max")
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")

    # Other filters
    availability = request.GET.get("availability")
    district_id = request.GET.get("district_id")
    user_type = request.GET.get("user_type")

    # Base queryset
    if user.user_type == "krisshak":
        queryset = BhooswamiProfile.objects.filter(district=user.krisshakprofile.district)
    elif user.user_type == "bhooswami":
        queryset = KrisshakProfile.objects.filter(district=user.bhooswamiprofile.district)
    elif user.user_type == "district_admin":
        try:
            queryset = CustomUser.objects.filter(district=user.districtadminprofile.district)
            if user_type:
                queryset = queryset.filter(user_type=user_type)
        except DistrictAdminProfile.DoesNotExist:
            return JsonResponse({"error": "District not found"}, status=404)
    elif user.user_type == "state_admin":
        try:
            queryset = CustomUser.objects.filter(district__state=user.stateadminprofile.state)
            if user_type:
                queryset = queryset.filter(user_type=user_type)
        except StateAdminProfile.DoesNotExist:
            return JsonResponse({"error": "State not found"}, status=404)
    else:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    model = queryset.model

    # Apply filters

    if district_id:
        queryset = queryset.filter(district_id=district_id)

    if age_min:
        if model == CustomUser:
            queryset = queryset.filter(age__gte=int(age_min))
        else:
            queryset = queryset.filter(user__age__gte=int(age_min))
    if age_max:
        if model == CustomUser:
            queryset = queryset.filter(age__lte=int(age_max))
        else:
            queryset = queryset.filter(user__age__lte=int(age_max))

    if specialization and model_has_field(model, "specialization"):
        queryset = queryset.filter(specialization__icontains=specialization)

    if requirements and model_has_field(model, "requirements"):
        queryset = queryset.filter(requirements__icontains=requirements)

    if land_location and model_has_field(model, "land_location"):
        queryset = queryset.filter(land_location__icontains=land_location)

    if experience_min and model_has_field(model, "experience"):
        queryset = queryset.filter(experience__gte=int(experience_min))
    if experience_max and model_has_field(model, "experience"):
        queryset = queryset.filter(experience__lte=int(experience_max))

    if land_area_min and model_has_field(model, "land_area"):
        queryset = queryset.filter(land_area__gte=float(land_area_min))
    if land_area_max and model_has_field(model, "land_area"):
        queryset = queryset.filter(land_area__lte=float(land_area_max))

    if price_min and model_has_field(model, "price"):
        queryset = queryset.filter(price__gte=float(price_min))
    if price_max and model_has_field(model, "price"):
        queryset = queryset.filter(price__lte=float(price_max))

    if availability and model_has_field(model, "availability"):
        queryset = queryset.filter(availability=True)

    # Ordering
    ordering_fields = []
    if model_has_field(model, "availability"):
        ordering_fields.append("-availability")
    if model_has_field(model, "ratings"):
        ordering_fields.append("-ratings")
    if ordering_fields:
        queryset = queryset.order_by(*ordering_fields)

    return JsonResponse({
        "filtered_users": [user.to_dict(request) for user in queryset]
    }, safe=False)