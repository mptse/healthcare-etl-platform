# apps/analytics/views.py
from django.shortcuts import render, redirect # Asegúrate de importar redirect
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .analytics import obtener_resumen_riesgo, listar_pacientes_criticos, obtener_promedios_clinicos

@login_required
@role_required(allowed_roles=['Analista'])
def dashboard_analista(request):
    resumen_qs = obtener_resumen_riesgo()
    resumen = {item['riesgo_enfermedad']: item['total'] for item in resumen_qs}

    datos_para_grafico = [
        resumen.get('Bajo', 0),
        resumen.get('Medio', 0),
        resumen.get('Crítico', 0),
    ]

    context = {
        'total_pacientes': sum(datos_para_grafico),
        'datos_riesgo': datos_para_grafico,
        'resumen_riesgo': resumen,
        'promedios': obtener_promedios_clinicos(),
    }
    return render(request, 'analytics/dashboard_analista.html', context)

@login_required
@role_required(allowed_roles=['Médico'])
def dashboard_medico(request):
    context = {'pacientes_alerta': listar_pacientes_criticos()}
    return render(request, 'analytics/dashboard_medico.html', context)

@login_required
@role_required(allowed_roles=['Admin'])
def dashboard_admin(request):
    return render(request, 'analytics/dashboard_admin.html')

# --- ESTA ES LA VISTA QUE FALTABA ---
@login_required
def dashboard_redirect(request):
    if request.user.groups.filter(name='Analista').exists():
        return redirect('dashboard_analista')
    elif request.user.groups.filter(name='Médico').exists():
        return redirect('dashboard_medico')
    elif request.user.groups.filter(name='Admin').exists():
        return redirect('dashboard_admin')
    else:
        return redirect('login')