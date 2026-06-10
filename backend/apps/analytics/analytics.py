import numpy as np
from django.db.models import Avg, Count, Q, StdDev, Max, Min
from apps.etl.models import RegistroClinico, Paciente


# ── KPIs básicos ────────────────────────────────────────────────────
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
    qs = RegistroClinico.objects.select_related('paciente').filter(
        Q(riesgo_enfermedad__in=['Crítico', 'Alto']) |
        Q(presion_sistolica__gt=180) |          # criterios del reto
        Q(glucosa__gt=300) |
        Q(saturacion_oxigeno__lt=85)
    ).order_by('-fecha_consulta')
    return qs[:limite] if limite else qs


# ── Estadística descriptiva completa ────────────────────────────────
def obtener_estadistica_descriptiva():
    """
    Media, mediana, moda, desviación estándar, min, max
    para las variables clínicas principales.
    """
    campos = [
        'glucosa', 'colesterol', 'imc', 'presion_sistolica',
        'presion_diastolica', 'frecuencia_cardiaca',
        'saturacion_oxigeno', 'temperatura', 'peso', 'altura'
    ]

    valores = RegistroClinico.objects.values_list(*campos)
    if not valores.exists():
        return {}

    arr = np.array(list(valores), dtype=float)
    resultado = {}

    for i, campo in enumerate(campos):
        col = arr[:, i]
        col_limpia = col[~np.isnan(col)]
        if len(col_limpia) == 0:
            continue

        # Moda manual (numpy no tiene moda directa)
        valores_unicos, conteos = np.unique(col_limpia, return_counts=True)
        moda = float(valores_unicos[np.argmax(conteos)])

        resultado[campo] = {
            'media':     round(float(np.mean(col_limpia)), 2),
            'mediana':   round(float(np.median(col_limpia)), 2),
            'moda':      round(moda, 2),
            'std':       round(float(np.std(col_limpia)), 2),
            'min':       round(float(np.min(col_limpia)), 2),
            'max':       round(float(np.max(col_limpia)), 2),
        }

    return resultado


# ── Segmentación ─────────────────────────────────────────────────────
def obtener_segmentacion():
    """Segmentación por edad, sexo, riesgo e IMC."""

    # Por sexo
    por_sexo = list(
        Paciente.objects.values('sexo').annotate(total=Count('id'))
    )

    # Por riesgo
    por_riesgo = list(
        RegistroClinico.objects.values('riesgo_enfermedad').annotate(total=Count('id'))
    )

    # Por grupo de edad
    registros = RegistroClinico.objects.select_related('paciente').values_list(
        'paciente__edad', flat=True
    )
    edades = list(registros)
    grupos_edad = {'0-18': 0, '19-35': 0, '36-50': 0, '51-65': 0, '65+': 0}
    for edad in edades:
        if edad <= 18:
            grupos_edad['0-18'] += 1
        elif edad <= 35:
            grupos_edad['19-35'] += 1
        elif edad <= 50:
            grupos_edad['36-50'] += 1
        elif edad <= 65:
            grupos_edad['51-65'] += 1
        else:
            grupos_edad['65+'] += 1

    # Por clasificación IMC
    grupos_imc = {
        'Bajo peso':   RegistroClinico.objects.filter(imc__lt=18.5).count(),
        'Normal':      RegistroClinico.objects.filter(imc__gte=18.5, imc__lt=25).count(),
        'Sobrepeso':   RegistroClinico.objects.filter(imc__gte=25, imc__lt=30).count(),
        'Obesidad':    RegistroClinico.objects.filter(imc__gte=30).count(),
    }

    return {
        'por_sexo':   por_sexo,
        'por_riesgo': por_riesgo,
        'por_edad':   grupos_edad,
        'por_imc':    grupos_imc,
    }


# ── KPIs admin completos ─────────────────────────────────────────────
def obtener_kpis_admin():
    total = RegistroClinico.objects.count()
    total_pacientes = Paciente.objects.count()

    return {
        'total_registros':   total,
        'total_pacientes':   total_pacientes,
        'criticos':          RegistroClinico.objects.filter(riesgo_enfermedad='Crítico').count(),
        'alto':              RegistroClinico.objects.filter(riesgo_enfermedad='Alto').count(),
        'medio':             RegistroClinico.objects.filter(riesgo_enfermedad='Medio').count(),
        'bajo':              RegistroClinico.objects.filter(riesgo_enfermedad='Bajo').count(),
        'fumadores':         RegistroClinico.objects.filter(fumador=True).count(),
        'hipertensos':       RegistroClinico.objects.filter(presion_sistolica__gt=140).count(),
        'diabeticos':        RegistroClinico.objects.filter(glucosa__gt=126).count(),
        'saturacion_baja':   RegistroClinico.objects.filter(saturacion_oxigeno__lt=90).count(),
        'promedios':         obtener_promedios_clinicos(),
    }


def obtener_estadisticas_medico():
    return RegistroClinico.objects.aggregate(
        total=Count('id'),
        criticos=Count('id', filter=Q(riesgo_enfermedad='Crítico')),
        hipertensos=Count('id', filter=Q(presion_sistolica__gt=140)),
        glucosa_alta=Count('id', filter=Q(glucosa__gt=126)),
        saturacion_baja=Count('id', filter=Q(saturacion_oxigeno__lt=90)),
    )