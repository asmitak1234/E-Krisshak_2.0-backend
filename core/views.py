from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils.translation import activate

def homepage(request):
    message = _("Welcome to E-Krisshak 2.0 !")
    return JsonResponse({"message": message})


def set_language(request, lang_code):
    """Allows users to change language preference"""
    if lang_code not in ['en', 'hi']:
        return JsonResponse({"error": "Invalid language code"}, status=400)

    activate(lang_code)
    response = JsonResponse({"message": "Language updated!"})
    response.set_cookie('preferred_language', lang_code)  # Stores preference
    return response
