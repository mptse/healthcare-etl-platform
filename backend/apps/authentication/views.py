from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Vista web tradicional (login HTML) ──────────────────────────────
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.groups.filter(name='Analista').exists():
                return redirect('dashboard_analista')
            elif user.groups.filter(name='Médico').exists():
                return redirect('dashboard_medico')
            else:
                return redirect('dashboard_admin')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})


# ── API REST: Login con JWT ──────────────────────────────────────────
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username y password son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'usuario': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'rol': user.role,
                'nombre_completo': user.get_full_name(),
            }
        })


# ── API REST: Perfil del usuario autenticado ─────────────────────────
class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'rol': user.role,
            'nombre_completo': user.get_full_name(),
            'especialidad': user.especialidad,
        })


# ── API REST: Logout (invalida refresh token) ────────────────────────
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'mensaje': 'Sesión cerrada correctamente.'})
        except Exception:
            return Response(
                {'error': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )