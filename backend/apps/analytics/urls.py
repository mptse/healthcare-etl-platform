# apps/analytics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Esta línea es la que faltaba para que /dashboard/ funcione:
    path('', views.dashboard_redirect, name='dashboard_principal'),
    
    # Tus rutas existentes:
    path('medico/', views.dashboard_medico, name='dashboard_medico'),
    path('analista/', views.dashboard_analista, name='dashboard_analista'),
    path('admin/', views.dashboard_admin, name='dashboard_admin'),
]