import pandas as pd
import numpy as np
import logging
from django.db import transaction
from .models import Paciente, RegistroClinico

logger = logging.getLogger(__name__)

def run_etl(file_path):
    try:
        # 1. Extracción
        df = pd.read_excel(file_path)
        
        # 2. Transformación: Limpieza básica
        # Normalizamos nombres de columnas para evitar errores de espacios o mayúsculas
        df.columns = df.columns.str.strip().str.lower()
        
        # Convertimos todo el contenido a minúsculas para consistencia
        df = df.map(lambda x: x.lower() if isinstance(x, str) else x)
        
        # Manejo de nulos: Media para números, "no especificado" para texto
        cols_num = df.select_dtypes(include=[np.number]).columns
        df[cols_num] = df[cols_num].fillna(df[cols_num].mean())
        df = df.fillna("no especificado")
        
        # 3. Carga masiva usando transacciones para integridad de datos
        with transaction.atomic():
            for _, row in df.iterrows():
                # Buscamos o creamos al paciente usando su 'identificacion' como llave única
                # Asegúrate de que en tu Excel exista la columna 'identificacion'
                paciente, created = Paciente.objects.get_or_create(
                    identificacion=str(row['identificacion']),
                    defaults={
                        'nombres': row['nombres'],
                        'apellidos': row['apellidos'],
                        'edad': int(row['edad']),
                        'sexo': row['sexo']
                    }
                )
                
                # Creamos el registro clínico asociado
                RegistroClinico.objects.create(
                    paciente=paciente,
                    peso=float(row['peso']),
                    altura=float(row['altura']),
                    imc=float(row['imc']),
                    presion_sistolica=int(row['presión_sistólica']),
                    presion_diastolica=int(row['presión_diastolica']),
                    frecuencia_cardiaca=int(row['frecuencia_cardiaca']),
                    glucosa=float(row['glucosa']),
                    colesterol=int(row['colesterol']),
                    saturacion_oxigeno=float(row['saturación_oxígeno']),
                    temperatura=float(row['temperatura']),
                    antecedentes_familiares=row['antecedentes_familiares'],
                    fumador=(str(row['fumador']).lower() == 'true' or str(row['fumador']) == '1'),
                    consumo_alcohol=(str(row['consumo_alcohol']).lower() == 'true' or str(row['consumo_alcohol']) == '1'),
                    actividad_fisica=row['actividad_física'],
                    diagnostico_preliminar=row['diagnóstico_preliminar'],
                    riesgo_enfermedad=row['riesgo_enfermedad'],
                    fecha_consulta=pd.to_datetime(row['fecha_consulta']).date()
                )
                
        logger.info("ETL finalizado con éxito.")
        return True

    except KeyError as e:
        logger.error(f"Error: La columna {e} no existe en el archivo Excel.")
        return False
    except Exception as e:
        logger.error(f"Error inesperado en ETL: {e}")
        return False

        