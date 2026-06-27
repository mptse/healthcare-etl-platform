import time
import unicodedata
import pandas as pd
import gender_guesser.detector as gender_detector
from django.db import transaction
from .models import Paciente, RegistroClinico

_detector = gender_detector.Detector(case_sensitive=False)


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


def inferir_sexo_por_nombre(nombre, sexo_original):
    try:
        primer_nombre = str(nombre).strip().split()[0]
        resultado = _detector.get_gender(primer_nombre)
        if resultado in ['male', 'mostly_male']:
            return 'Masculino'
        elif resultado in ['female', 'mostly_female']:
            return 'Femenino'
        else:
            return normalizar_sexo(sexo_original)
    except:
        return normalizar_sexo(sexo_original)


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
    ETL optimizado con bulk_create — una sola transacción a la BD.
    """
    logs = []
    inicio = time.time()
    errores = 0
    sexos_corregidos = 0

    try:
        # ── EXTRACT ──────────────────────────────────────────────────
        logs.append("EXTRACT: Leyendo archivo...")
        if str(file_path).endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        df.columns = [normalizar_columna(c) for c in df.columns]
        logs.append(f"  → {len(df)} filas encontradas.")

        # ── TRANSFORM ────────────────────────────────────────────────
        logs.append("TRANSFORM: Limpiando datos...")
        total_original = len(df)
        df = df.dropna(subset=['id_paciente', 'fecha_consulta'])
        df = df.sort_values(by=['id_paciente', 'fecha_consulta'])
        df = df.drop_duplicates(subset=['id_paciente', 'fecha_consulta'])
        duplicados = total_original - len(df)

        df = df.set_index('id_paciente')
        df = df.groupby(level=0).ffill()
        df = df.reset_index()

        logs.append(f"  → {duplicados} duplicados eliminados.")
        logs.append(f"  → {len(df)} registros limpios para cargar.")

        # ── LOAD — preparar datos en memoria ─────────────────────────
        logs.append("LOAD: Preparando datos en memoria...")

        # Cargar pacientes existentes de una sola query
        pacientes_existentes = {
            p.identificacion: p for p in Paciente.objects.all()
        }

        # Cargar registros existentes (paciente_id, fecha) de una sola query
        registros_existentes = set(
            RegistroClinico.objects.values_list('paciente__identificacion', 'fecha_consulta')
        )

        nuevos_pacientes = {}
        registros_a_crear = []

        for _, row in df.iterrows():
            try:
                p_id = str(row.get('id_paciente', '')).strip()
                if not p_id:
                    errores += 1
                    continue

                # Preparar paciente nuevo si no existe
                if p_id not in pacientes_existentes and p_id not in nuevos_pacientes:
                    sexo_original = row.get('sexo')
                    sexo_inferido = inferir_sexo_por_nombre(
                        row.get('nombres', ''), sexo_original
                    )
                    if sexo_inferido != normalizar_sexo(sexo_original):
                        sexos_corregidos += 1

                    nuevos_pacientes[p_id] = Paciente(
                        identificacion=p_id,
                        nombres=str(row.get('nombres', 'N/A')),
                        apellidos=str(row.get('apellidos', 'N/A')),
                        edad=int(limpiar_numerico(row.get('edad'), 30)),
                        sexo=sexo_inferido,
                    )

                # Preparar registro clínico si no existe
                fecha = pd.to_datetime(row['fecha_consulta']).date()
                if (p_id, fecha) not in registros_existentes:
                    registros_a_crear.append((p_id, fecha, row))

            except Exception as e:
                errores += 1
                logs.append(f"  ⚠ Fila omitida: {e}")

        # ── Insertar pacientes nuevos de una vez ──────────────────────
        logs.append(f"  → Creando {len(nuevos_pacientes)} pacientes nuevos...")
        if nuevos_pacientes:
            with transaction.atomic():
                creados = Paciente.objects.bulk_create(
                    list(nuevos_pacientes.values()),
                    ignore_conflicts=True
                )

        # Recargar pacientes para tener los IDs correctos
        todos_pacientes = {
            p.identificacion: p for p in Paciente.objects.all()
        }

        # ── Insertar registros clínicos de una vez ────────────────────
        logs.append(f"  → Creando {len(registros_a_crear)} registros clínicos...")
        objetos_registro = []
        for p_id, fecha, row in registros_a_crear:
            if p_id not in todos_pacientes:
                continue
            objetos_registro.append(RegistroClinico(
                paciente=todos_pacientes[p_id],
                fecha_consulta=fecha,
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
            ))

        with transaction.atomic():
            RegistroClinico.objects.bulk_create(
                objetos_registro,
                ignore_conflicts=True
            )

        creados_count = len(objetos_registro)
        logs.append(f"  → {sexos_corregidos} sexos corregidos por nombre.")
        logs.append(f"  → {creados_count} registros insertados | {errores} errores.")

        # ── RECALCULAR RIESGOS ────────────────────────────────────────
        logs.append("RIESGOS: Recalculando con reglas clínicas...")
        try:
            from apps.ml.trainer import recalcular_riesgos_bd
            actualizados = recalcular_riesgos_bd()
            logs.append(f"  → {actualizados} riesgos recalculados.")
        except Exception as e:
            logs.append(f"  ⚠ Error riesgos: {e}")

        # ── REENTRENAR ML ─────────────────────────────────────────────
        logs.append("ML: Reentrenando modelo...")
        try:
            from apps.ml.trainer import entrenar_modelo
            ml_resultado, ml_error = entrenar_modelo()
            if ml_resultado:
                logs.append(f"  → Accuracy: {ml_resultado['accuracy']}%")
            else:
                logs.append(f"  ⚠ {ml_error}")
        except Exception as e:
            logs.append(f"  ⚠ Error ML: {e}")

        tiempo = round(time.time() - inicio, 2)
        logs.append(f"ÉXITO: ETL completado en {tiempo}s.")

        return {
            'exito':                True,
            'registros_procesados': creados_count,
            'registros_fallidos':   errores,
            'tiempo_ejecucion':     tiempo,
            'log_detalle':          '\n'.join(logs),
            'mensaje_error':        '',
        }

    except Exception as e:
        import traceback
        tiempo = round(time.time() - inicio, 2)
        logs.append(f"ERROR CRÍTICO: {e}")
        return {
            'exito':                False,
            'registros_procesados': 0,
            'registros_fallidos':   errores,
            'tiempo_ejecucion':     tiempo,
            'log_detalle':          '\n'.join(logs),
            'mensaje_error':        traceback.format_exc(),
        }