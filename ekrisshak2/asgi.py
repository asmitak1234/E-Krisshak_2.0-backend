"""
ASGI config for ekrisshak2 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ekrisshak2.settings')

import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.routing import websocket_urlpatterns
from notifications.middleware import TokenAuthMiddleware


application = ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    )
})

