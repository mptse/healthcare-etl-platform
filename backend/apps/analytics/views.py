from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .analytics import (
    obtener_resumen_riesgo,
    listar_pacientes_criticos,
    obtener_promedios_clinicos,
    obtener_kpis_admin,
    obtener_estadisticas_medico,
)

@login_required
@role_required(allowed_roles=['Analista'])
def dashboard_analista(request):
    resumen_qs = obtener_resumen_riesgo()
    resumen = {item['riesgo_enfermedad']: item['total'] for item in resumen_qs}

    context = {
        'total_pacientes': sum(resumen.values()),
        'datos_riesgo': [
            resumen.get('Bajo', 0),
            resumen.get('Medio', 0),
            resumen.get('Alto', 0),
            resumen.get('Crítico', 0),
        ],
        'resumen_riesgo': resumen,
        'promedios': obtener_promedios_clinicos(),
        'pacientes_criticos': listar_pacientes_criticos()[:5],
    }
    return render(request, 'analytics/dashboard_analista.html', context)

@login_required
@role_required(allowed_roles=['Médico'])
def dashboard_medico(request):
    stats = obtener_estadisticas_medico()
    context = {
        'pacientes_alerta': listar_pacientes_criticos(),
        'total_criticos': listar_pacientes_criticos().count(),
        'stats': stats,
    }
    return render(request, 'analytics/dashboard_medico.html', context)

@login_required
@role_required(allowed_roles=['Admin'])
def dashboard_admin(request):
    context = obtener_kpis_admin()
    return render(request, 'analytics/dashboard_admin.html', context)

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