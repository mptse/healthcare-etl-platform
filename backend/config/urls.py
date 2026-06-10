from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from apps.analytics.views import (
    KPIsAPIView, EstadisticaDescriptivaAPIView,
    SegmentacionAPIView, PacientesCriticosAPIView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login')),

    # Vistas web
    path('auth/',      include('apps.authentication.urls')),
    path('dashboard/', include('apps.analytics.urls')),
    path('ml/',        include('apps.ml.urls')),

    # API REST
    path('api/auth/',  include('apps.authentication.urls')),
    path('api/etl/',   include('apps.etl.urls')),

    # API Analytics
    path('api/dashboard/kpis/',         KPIsAPIView.as_view(),                name='api-kpis'),
    path('api/dashboard/estadisticas/', EstadisticaDescriptivaAPIView.as_view(), name='api-estadisticas'),
    path('api/dashboard/segmentacion/', SegmentacionAPIView.as_view(),        name='api-segmentacion'),
    path('api/dashboard/criticos/',     PacientesCriticosAPIView.as_view(),   name='api-criticos'),
]