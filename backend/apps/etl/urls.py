from django.urls import path
from .views import EjecutarETLView, HistorialETLView, DetalleETLView, historial_web, exportar_csv, exportar_excel

urlpatterns = [
    path('run/',       EjecutarETLView.as_view(),      name='etl-run'),
    path('historial/', HistorialETLView.as_view(),     name='etl-historial'),
    path('historial/<int:pk>/', DetalleETLView.as_view(), name='etl-detalle'),


     # Vistas web
    path('logs/',                   historial_web,               name='historial_etl'),
    path('exportar/csv/',           exportar_csv,                name='exportar_csv'),
    path('exportar/excel/',         exportar_excel,              name='exportar_excel'),
]


