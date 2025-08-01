"""
URL configuration for ekrisshak2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

def health_check(request):
    return JsonResponse({"ok": True})

urlpatterns = [
    path("", health_check),   
    path('admin/', admin.site.urls),  
    path('api/users/', include('users.urls')),  # User authentication & role-based access
    path('api/contact/', include('contact.urls')),  # Contact messages & admin escalation
    path('api/appointments/', include('appointments.urls')),  # Scheduling system
    path('api/calender/', include('calender.urls')),  # Calendar integration for events
    path('api/notifications/', include('notifications.urls')),  # Live alerts & WebSocket updates
    path('api/payments/', include('payments.urls')),  # Razorpay integration & transactions
    path('api/core/', include('core.urls')),
    # path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    path('api/search/', include('search.urls')),
]

#     re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
