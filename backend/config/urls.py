from django.contrib import admin
from django.urls import path, include
# ¡Aquí está el import que faltaba!
from django.shortcuts import redirect 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Ahora 'redirect' ya está definido y funcionará correctamente
    path('', lambda request: redirect('login')), 
    path('dashboard/', include('apps.analytics.urls')),
    path('auth/', include('apps.authentication.urls')),
    path('ml/', include('apps.ml.urls')),
]