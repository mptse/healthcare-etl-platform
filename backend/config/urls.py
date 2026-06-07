from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Mantenemos tu login, pero es buena práctica darle un prefijo como 'auth/'
    # Así separas claramente las rutas de seguridad de las rutas de negocio
    path('auth/', include('apps.authentication.urls')), 
    
    # Aquí integramos la nueva app de analítica
    path('dashboard/', include('apps.analytics.urls')),
]