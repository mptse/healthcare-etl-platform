from django.urls import path
from .views import EjecutarETLView, HistorialETLView, DetalleETLView

urlpatterns = [
    path('run/',       EjecutarETLView.as_view(),      name='etl-run'),
    path('historial/', HistorialETLView.as_view(),     name='etl-historial'),
    path('historial/<int:pk>/', DetalleETLView.as_view(), name='etl-detalle'),
]