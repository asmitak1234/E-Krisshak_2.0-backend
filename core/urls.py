from django.urls import path
from .views import set_language

urlpatterns = [
    path('set-language/<str:lang_code>/', set_language, name='set-language'),
]
