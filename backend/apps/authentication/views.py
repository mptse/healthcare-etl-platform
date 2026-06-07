

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        # Aquí capturas los datos del formulario (ajusta según tus nombres de campo)
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # --- LÓGICA DE REDIRECCIÓN POR ROL ---
            # Esto cumple con el criterio de Dashboard y Seguridad
            if user.groups.filter(name='Médico').exists():
                return redirect('dashboard_medico')
            
            elif user.groups.filter(name='Analista').exists():
                return redirect('dashboard_analista')
            
            elif user.groups.filter(name='Admin').exists():
                return redirect('dashboard_admin')
            
            else:
                # Si el usuario no tiene rol asignado, enviarlo a una home estándar
                return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            
    return render(request, 'authentication/login.html')