from django.urls import path
from . import views

urlpatterns = [
    path('', views.ml_dashboard, name='ml_dashboard'),
    path('predecir-paciente/', views.predecir_paciente, name='predecir_paciente'),
]