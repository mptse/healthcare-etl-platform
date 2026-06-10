from django.urls import path
from . import views

urlpatterns = [
    # Vistas web
    path('',         views.dashboard_redirect, name='dashboard_principal'),
    path('medico/',  views.dashboard_medico,   name='dashboard_medico'),
    path('analista/', views.dashboard_analista, name='dashboard_analista'),
    path('admin/',   views.dashboard_admin,    name='dashboard_admin'),
]