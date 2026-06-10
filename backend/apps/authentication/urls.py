from django.urls import path
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Vistas web
    path('login/',  views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # API REST
    path('api/login/',   views.LoginAPIView.as_view(),  name='api-login'),
    path('api/logout/',  views.LogoutAPIView.as_view(), name='api-logout'),
    path('api/perfil/',  views.PerfilView.as_view(),    name='api-perfil'),
    path('api/refresh/', TokenRefreshView.as_view(),    name='api-refresh'),
]