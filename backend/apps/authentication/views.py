from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Lógica de redirección según el grupo del usuario
            if user.groups.filter(name='Analista').exists():
                return redirect('dashboard_analista')
            elif user.groups.filter(name='Médico').exists():
                return redirect('dashboard_medico')
            else:
                return redirect('dashboard_admin')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})