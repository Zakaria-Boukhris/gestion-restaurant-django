"""
URL configuration for gestion_restaurant project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_custom_admin(request):
    """Redirection vers l'interface admin personnalisée"""
    return redirect('/admin-custom/')

urlpatterns = [
    path('admin/', redirect_to_custom_admin),
   
    path('', include('restaurant.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
