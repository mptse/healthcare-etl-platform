import time
import unicodedata
import pandas as pd
from django.db import transaction
from .models import Paciente, RegistroClinico


def normalizar_columna(nombre):
    nombre = str(nombre).lower().strip().replace(' ', '_')
    nombre = unicodedata.normalize('NFKD', nombre)
    nombre = ''.join(c for c in nombre if not unicodedata.combining(c))
    return nombre


def limpiar_numerico(valor, default=0.0):
    mapeo = {'treinta': 30, 'veinte': 20, 'diez': 10, 'cuarenta': 40, 'cincuenta': 50}
    try:
        if pd.isna(valor):
            return float(default)
        if isinstance(valor, str):
            val_limpio = valor.lower().strip()
            if val_limpio in mapeo:
                return float(mapeo[val_limpio])
            return float(val_limpio)
        return float(valor)
    except:
        return float(default)


def normalizar_sexo(valor):
    if pd.isna(valor):
        return 'N/A'
    v = str(valor).strip().lower()
    if v in ['m', 'masculino', 'male', 'hombre']:
        return 'Masculino'
    elif v in ['f', 'femenino', 'female', 'mujer']:
        return 'Femenino'
    return str(valor).strip()


def normalizar_riesgo(valor):
    if pd.isna(valor):
        return 'Bajo'
    v = str(valor).strip().lower()
    if 'criti' in v or 'críti' in v:
        return 'Crítico'
    elif 'alto' in v:
        return 'Alto'
    elif 'medio' in v or 'media' in v:
        return 'Medio'
    elif 'bajo' in v:
        return 'Bajo'
    return str(valor).strip()


def run_etl(file_path):
    """
    Retorna un dict con: exito, registros_procesados, registros_fallidos,
    tiempo_ejecucion, log_detalle, mensaje_error
    """
    logs = []
    inicio = time.time()
    registros_fallidos = 0

    try:
        logs.append("EXTRACT: Leyendo archivo...")
        df = pd.read_excel(file_path)
        logs.append(f"  → {len(df)} filas encontradas en el archivo.")

        df.columns = [normalizar_columna(c) for c in df.columns]
        logs.append(f"  → Columnas: {list(df.columns)}")

        # TRANSFORM
        logs.append("TRANSFORM: Limpiando datos...")
        antes = len(df)
        df = df.dropna(subset=['id_paciente', 'fecha_consulta'])
        df = df.sort_values(by=['id_paciente', 'fecha_consulta'])
        df = df.drop_duplicates(subset=['id_paciente', 'fecha_consulta'])
        eliminados = antes - len(df)
        logs.append(f"  → {eliminados} duplicados/nulos eliminados.")

        df = df.set_index('id_paciente')
        df = df.groupby(level=0).ffill()
        df = df.reset_index()
        logs.append(f"  → {len(df)} registros limpios listos para cargar.")

        # LOAD
        logs.append("LOAD: Insertando en base de datos...")
        pacientes_db = {p.identificacion: p for p in Paciente.objects.all()}
        registros_a_crear = []

        for _, row in df.iterrows():
            try:
                p_id = str(row.get('id_paciente', '')).strip()
                if not p_id:
                    registros_fallidos += 1
                    continue

                if p_id not in pacientes_db:
                    paciente = Paciente.objects.create(
                        identificacion=p_id,
                        nombres=str(row.get('nombres', 'N/A')),
                        apellidos=str(row.get('apellidos', 'N/A')),
                        edad=int(limpiar_numerico(row.get('edad'), 30)),
                        sexo=normalizar_sexo(row.get('sexo'))
                    )
                    pacientes_db[p_id] = paciente

                registros_a_crear.append(RegistroClinico(
                    paciente=pacientes_db[p_id],
                    peso=limpiar_numerico(row.get('peso'), 70.0),
                    altura=limpiar_numerico(row.get('altura'), 1.70),
                    imc=limpiar_numerico(row.get('imc'), 0.0),
                    presion_sistolica=int(limpiar_numerico(row.get('presion_sistolica'), 120)),
                    presion_diastolica=int(limpiar_numerico(row.get('presion_diastolica'), 80)),
                    frecuencia_cardiaca=int(limpiar_numerico(row.get('frecuencia_cardiaca'), 70)),
                    glucosa=limpiar_numerico(row.get('glucosa'), 90.0),
                    colesterol=int(limpiar_numerico(row.get('colesterol'), 150)),
                    saturacion_oxigeno=limpiar_numerico(row.get('saturacion_oxigeno'), 98.0),
                    temperatura=limpiar_numerico(row.get('temperatura'), 36.5),
                    antecedentes_familiares=str(row.get('antecedentes_familiares', 'Ninguno')),
                    fumador=str(row.get('fumador', '')).lower() in ['true', '1', 'si', 't', 1],
                    consumo_alcohol=str(row.get('consumo_alcohol', '')).lower() in ['true', '1', 'si', 't', 1],
                    actividad_fisica=str(row.get('actividad_fisica', 'N/A')),
                    diagnostico_preliminar=str(row.get('diagnostico_preliminar', 'N/A')),
                    riesgo_enfermedad=normalizar_riesgo(row.get('riesgo_enfermedad')),
                    fecha_consulta=pd.to_datetime(row['fecha_consulta']).date()
                ))
            except Exception as e:
                registros_fallidos += 1
                logs.append(f"  ⚠ Fila omitida: {e}")

        with transaction.atomic():
            RegistroClinico.objects.bulk_create(registros_a_crear)

        tiempo = round(time.time() - inicio, 2)
        logs.append(f"ÉXITO: {len(registros_a_crear)} registros cargados en {tiempo}s.")

        return {
            'exito': True,
            'registros_procesados': len(registros_a_crear),
            'registros_fallidos': registros_fallidos,
            'tiempo_ejecucion': tiempo,
            'log_detalle': '\n'.join(logs),
            'mensaje_error': '',
        }

    except Exception as e:
        import traceback
        tiempo = round(time.time() - inicio, 2)
        logs.append(f"ERROR CRÍTICO: {e}")
        return {
            'exito': False,
            'registros_procesados': 0,
            'registros_fallidos': registros_fallidos,
            'tiempo_ejecucion': tiempo,
            'log_detalle': '\n'.join(logs),
            'mensaje_error': traceback.format_exc(),
        }