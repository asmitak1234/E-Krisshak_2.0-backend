from django.urls import path
from .views import seasonal_crop_suggestions, ai_crop_suggestions, get_smart_suggestions, search_bhooswamis,search_krisshaks

urlpatterns = [
    path('seasonal-crops/', seasonal_crop_suggestions, name='seasonal-crops'),
    path('ai-crop-suggestions/', ai_crop_suggestions, name='ai-crop-suggestions'),
    path('search-suggestions/', get_smart_suggestions, name='search-suggestions'),
    path('search-krisshaks/', search_krisshaks, name='search-krisshaks'),
    path('search-bhooswamis/', search_bhooswamis, name='search-bhooswamis'),
]
