from django.utils.translation import get_language
import logging
from django.conf import settings
from django.core.cache import cache
import re

def get_user_language(request):
    """Detect user's preferred language"""
    return request.LANGUAGE_CODE if hasattr(request, "LANGUAGE_CODE") else "en"


def log_event(event, message):
    """Log system events"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"{event}: {message}")

def log_error(module, error_message):
    """Log errors centrally for debugging"""
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(module)
    logger.error(error_message)


def get_default_language():
    """Return system default language"""
    return settings.LANGUAGE_CODE


def get_cached_data(key):
    """Retrieve cached data"""
    return cache.get(key)

def set_cached_data(key, value, timeout=300):
    """Store data in cache"""
    cache.set(key, value, timeout)

def delete_cached_data(key):
    """Remove cached data"""
    cache.delete(key)


def sanitize_input(user_input):
    """Removes special characters to prevent security vulnerabilities"""
    return re.sub(r'[^a-zA-Z0-9\s]', '', user_input)

def get_core_setting(setting_name, default=None):
    """Retrieve settings dynamically"""
    return getattr(settings, setting_name, default)