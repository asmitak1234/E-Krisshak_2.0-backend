from django.utils.translation import activate
from django.contrib.auth.middleware import get_user

class LanguageMiddleware:
    """Middleware to apply preferred language based on cookies or user profile"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = get_user(request)  # Ensure user is fetched safely

        if user.is_authenticated and hasattr(user, 'preferred_language'):
            preferred_language = user.preferred_language
        else:
            preferred_language = request.COOKIES.get('preferred_language', 'en')

        activate(preferred_language)  # Apply language dynamically
        
        response = self.get_response(request)
        return response
