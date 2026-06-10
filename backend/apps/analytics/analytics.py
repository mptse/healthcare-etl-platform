from django.db.models import Avg, Count, Q
from apps.etl.models import RegistroClinico, Paciente

def obtener_resumen_riesgo():
    return RegistroClinico.objects.values('riesgo_enfermedad').annotate(total=Count('id'))

def obtener_promedios_clinicos():
    return RegistroClinico.objects.aggregate(
        promedio_glucosa=Avg('glucosa'),
        promedio_colesterol=Avg('colesterol'),
        promedio_imc=Avg('imc'),
        promedio_presion_sis=Avg('presion_sistolica'),
        promedio_frecuencia=Avg('frecuencia_cardiaca'),
        promedio_saturacion=Avg('saturacion_oxigeno'),
    )

def listar_pacientes_criticos(limite=None):
    return RegistroClinico.objects.select_related('paciente').filter(
        riesgo_enfermedad__in=['Crítico', 'Alto']
    ).order_by('-fecha_consulta')[:limite]

def obtener_kpis_admin():
    total = RegistroClinico.objects.count()
    total_pacientes = Paciente.objects.count()
    criticos = RegistroClinico.objects.filter(riesgo_enfermedad='Crítico').count()
    alto = RegistroClinico.objects.filter(riesgo_enfermedad='Alto').count()
    medio = RegistroClinico.objects.filter(riesgo_enfermedad='Medio').count()
    bajo = RegistroClinico.objects.filter(riesgo_enfermedad='Bajo').count()
    fumadores = RegistroClinico.objects.filter(fumador=True).count()
    hipertensos = RegistroClinico.objects.filter(presion_sistolica__gt=140).count()
    diabeticos = RegistroClinico.objects.filter(glucosa__gt=126).count()

    return {
        'total_registros': total,
        'total_pacientes': total_pacientes,
        'criticos': criticos,
        'alto': alto,
        'medio': medio,
        'bajo': bajo,
        'fumadores': fumadores,
        'hipertensos': hipertensos,
        'diabeticos': diabeticos,
        'promedios': obtener_promedios_clinicos(),
    }

def obtener_estadisticas_medico():
    return RegistroClinico.objects.aggregate(
        total=Count('id'),
        criticos=Count('id', filter=Q(riesgo_enfermedad='Crítico')),
        hipertensos=Count('id', filter=Q(presion_sistolica__gt=140)),
        glucosa_alta=Count('id', filter=Q(glucosa__gt=126)),
        saturacion_baja=Count('id', filter=Q(saturacion_oxigeno__lt=90)),
    )