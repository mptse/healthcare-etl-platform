import time
import unicodedata
import pandas as pd
from django.db import transaction
from .models import Paciente, RegistroClinico, ETLLog


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


def run_etl(file_path, usuario=None):
    log = ETLLog.objects.create(
        archivo_fuente=file_path,
        usuario=usuario,
        estado='en_proceso',
    )
    inicio = time.time()

    try:
        print("1. Leyendo archivo...")
        df = pd.read_excel(file_path) if str(file_path).endswith('.xlsx') else pd.read_csv(file_path)
        df.columns = [normalizar_columna(c) for c in df.columns]
        print("   Columnas detectadas:", list(df.columns))

        print("2. Procesando datos...")
        total_original = len(df)
        df = df.dropna(subset=['id_paciente', 'fecha_consulta'])
        df = df.sort_values(by=['id_paciente', 'fecha_consulta'])
        df_sin_duplicados = df.drop_duplicates(subset=['id_paciente', 'fecha_consulta'])
        duplicados = total_original - len(df_sin_duplicados)
        df = df_sin_duplicados

        df = df.set_index('id_paciente')
        df = df.groupby(level=0).ffill()
        df = df.reset_index()

        print(f"3. Procesando {len(df)} registros...")

        pacientes_db = {p.identificacion: p for p in Paciente.objects.all()}
        procesados = 0
        actualizados = 0
        creados = 0
        errores = 0

        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    p_id = str(row.get('id_paciente', '')).strip()
                    if not p_id:
                        continue

                    # Crear o actualizar paciente
                    if p_id not in pacientes_db:
                        paciente = Paciente.objects.create(
                            identificacion=p_id,
                            nombres=str(row.get('nombres', 'N/A')),
                            apellidos=str(row.get('apellidos', 'N/A')),
                            edad=int(limpiar_numerico(row.get('edad'), 30)),
                            sexo=normalizar_sexo(row.get('sexo'))
                        )
                        pacientes_db[p_id] = paciente
                    else:
                        # Actualizar datos del paciente si cambiaron
                        
                        paciente = pacientes_db[p_id]
                        paciente.nombres = str(row.get('nombres', paciente.nombres))
                        paciente.apellidos = str(row.get('apellidos', paciente.apellidos))
                        paciente.edad = int(limpiar_numerico(row.get('edad'), paciente.edad))
                        paciente.sexo = normalizar_sexo(row.get('sexo')) or paciente.sexo
                        paciente.save(update_fields=['nombres', 'apellidos', 'edad', 'sexo'])

                    fecha = pd.to_datetime(row['fecha_consulta']).date()

                    campos = dict(
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
                    )

                    # get_or_create evita duplicados contra la BD
                    registro, fue_creado = RegistroClinico.objects.get_or_create(
                        paciente=pacientes_db[p_id],
                        fecha_consulta=fecha,
                        defaults=campos
                    )

                    if fue_creado:
                        creados += 1
                    else:
                        # Si ya existe, actualiza los campos
                        for campo, valor in campos.items():
                            setattr(registro, campo, valor)
                        registro.save()
                        actualizados += 1

                    procesados += 1

                except Exception as e:
                    errores += 1
                    print(f"Error en fila: {e}")

        tiempo = round(time.time() - inicio, 2)

        log.registros_procesados = procesados
        log.registros_fallidos = errores
        log.tiempo_ejecucion = tiempo
        log.estado = 'exitoso'
        log.log_detalle = f"Creados: {creados} | Actualizados: {actualizados} | Duplicados en archivo: {duplicados}"
        log.mensaje_error = ''
        log.save()

        print(f"¡ÉXITO! Creados: {creados} | Actualizados: {actualizados} | Errores: {errores} | Tiempo: {tiempo}s")
        return True

    except Exception as e:
        import traceback
        tiempo = round(time.time() - inicio, 2)
        log.tiempo_ejecucion = tiempo
        log.estado = 'fallido'
        log.mensaje_error = str(e)
        log.save()
        print(f"ERROR en ETL: {e}")
        traceback.print_exc()
        return False