
from django.db.models import Avg, Count
from apps.etl.models import RegistroClinico

def obtener_resumen_riesgo():
    """
    Retorna la cantidad de pacientes por nivel de riesgo.
    Útil para crear gráficos de torta o barras en el dashboard.
    """
    return RegistroClinico.objects.values('riesgo_enfermedad').annotate(total=Count('id'))

def obtener_promedios_clinicos():
    """
    Calcula los promedios generales de salud del dataset.
    Permite comparar el estado de salud general de la población.
    """
    return RegistroClinico.objects.aggregate(
        promedio_glucosa=Avg('glucosa'),
        promedio_colesterol=Avg('colesterol'),
        promedio_imc=Avg('imc'),
        promedio_presion_sis=Avg('presion_sistolica')
    )

def listar_pacientes_criticos(limite=10):
    """
    Filtra los pacientes con riesgo 'Crítico' o 'Alto' 
    para mostrar en la tabla de alertas del dashboard.
    """
    return RegistroClinico.objects.filter(
        riesgo_enfermedad__in=['Crítico', 'Alto']
    ).order_by('-fecha_consulta')[:limite]