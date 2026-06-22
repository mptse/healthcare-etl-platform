from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .decorators import role_required
from .analytics import (
    obtener_resumen_riesgo, listar_pacientes_criticos,
    obtener_promedios_clinicos, obtener_kpis_admin,
    obtener_estadisticas_medico, obtener_estadistica_descriptiva,
    obtener_segmentacion,
)
from apps.etl.models import RegistroClinico


@login_required
@role_required(allowed_roles=['Analista'])
def dashboard_analista(request):
    resumen_qs = obtener_resumen_riesgo()
    resumen = {item['riesgo_enfermedad']: item['total'] for item in resumen_qs}
    segmentacion = obtener_segmentacion()
    estadisticas = obtener_estadistica_descriptiva()

    context = {
        'total_pacientes': sum(resumen.values()),
        'datos_riesgo': [
            resumen.get('Bajo', 0), resumen.get('Medio', 0),
            resumen.get('Alto', 0), resumen.get('Crítico', 0),
        ],
        'resumen_riesgo': resumen,
        'promedios': obtener_promedios_clinicos(),
        'pacientes_criticos': listar_pacientes_criticos(limite=10),
        'segmentacion': segmentacion,
        'estadisticas': estadisticas,
        'datos_sexo': [s['total'] for s in segmentacion['por_sexo']],
        'labels_sexo': [s['sexo'] for s in segmentacion['por_sexo']],
        'datos_edad': list(segmentacion['por_edad'].values()),
        'labels_edad': list(segmentacion['por_edad'].keys()),
        'datos_imc': list(segmentacion['por_imc'].values()),
        'labels_imc': list(segmentacion['por_imc'].keys()),
    }
    return render(request, 'analytics/dashboard_analista.html', context)


@login_required
@role_required(allowed_roles=['Médico'])
def dashboard_medico(request):
    # Trae todos los pacientes — el filtrado es en tiempo real con JS
    qs = RegistroClinico.objects.select_related('paciente').all().order_by('-fecha_consulta')
    context = {
        'pacientes_alerta': qs,
        'stats': obtener_estadisticas_medico(),
    }
    return render(request, 'analytics/dashboard_medico.html', context)


@login_required
@role_required(allowed_roles=['Admin'])
def dashboard_admin(request):
    segmentacion = obtener_segmentacion()
    context = obtener_kpis_admin()
    context.update({
        'segmentacion': segmentacion,
        'datos_sexo': [s['total'] for s in segmentacion['por_sexo']],
        'labels_sexo': [s['sexo'] for s in segmentacion['por_sexo']],
        'datos_edad': list(segmentacion['por_edad'].values()),
        'labels_edad': list(segmentacion['por_edad'].keys()),

    })

    context['pacientes_lista'] = RegistroClinico.objects.select_related('paciente').order_by('-fecha_consulta')

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


class KPIsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(obtener_kpis_admin())

class EstadisticaDescriptivaAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(obtener_estadistica_descriptiva())

class SegmentacionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(obtener_segmentacion())

class PacientesCriticosAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        pacientes = listar_pacientes_criticos()
        data = [{
            'id': r.id,
            'paciente': f"{r.paciente.nombres} {r.paciente.apellidos}",
            'riesgo': r.riesgo_enfermedad,
            'presion_sistolica': r.presion_sistolica,
            'glucosa': r.glucosa,
            'saturacion_oxigeno': r.saturacion_oxigeno,
            'fecha_consulta': str(r.fecha_consulta),
        } for r in pacientes[:100]]
        return Response({'total': len(data), 'pacientes': data})