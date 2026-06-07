# apps/analytics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Al estar incluido bajo 'dashboard/' en el archivo anterior, 
    # estas rutas quedarían como: /dashboard/medico/, /dashboard/analista/, etc.
    path('medico/', views.medico_dashboard, name='dashboard_medico'),
    path('analista/', views.analista_dashboard, name='dashboard_analista'),
    path('admin/', views.admin_dashboard, name='dashboard_admin'),
]