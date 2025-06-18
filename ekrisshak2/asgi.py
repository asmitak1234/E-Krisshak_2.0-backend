"""
ASGI config for ekrisshak2 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django
from channels.routing import get_default_application
from .routing import application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ekrisshak2.settings')
django.setup()
application = get_default_application()
