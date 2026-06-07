# apps/analytics/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .analytics import obtener_resumen_riesgo, listar_pacientes_criticos, obtener_promedios_clinicos

@login_required
@role_required(allowed_roles=['Médico'])
def medico_dashboard(request):
    context = {'pacientes_alerta': listar_pacientes_criticos()}
    return render(request, 'analytics/medico_dashboard.html', context)

@login_required
@role_required(allowed_roles=['Analista'])
def analista_dashboard(request):
    context = {
        'resumen_riesgo': obtener_resumen_riesgo(),
        'promedios': obtener_promedios_clinicos()
    }
    return render(request, 'analytics/analista_dashboard.html', context)

@login_required
@role_required(allowed_roles=['Admin'])
def admin_dashboard(request):
    return render(request, 'analytics/admin_dashboard.html')