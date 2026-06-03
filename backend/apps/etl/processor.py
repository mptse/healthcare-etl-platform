import pandas as pd
import time
from django.db import DatabaseError
from apps.etl.models import Paciente, RegistroClinico

def run_etl():
    file_path = r'C:\Users\GLORIA ORTIZ\healthcare-etl-platform\backend\dataset_clinico_etl_1800_registros.xlsx'
    
    print("Cargando archivo...")
    df = pd.read_excel(file_path)
    df = df.drop_duplicates()
    
   # Limpieza de nulos y conversión a tipos de datos correctos
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna('sin dato').astype(str).str.lower().str.strip()

    # --- NUEVA LÓGICA DE CONVERSIÓN BOOLEANA ---
    def to_bool(val):
        if isinstance(val, bool): return val
        return str(val).lower() in ['true', 't', '1', 'si', 'sí']

    df['fumador'] = df['fumador'].apply(to_bool)
    df['consumo_alcohol'] = df['consumo_alcohol'].apply(to_bool)
    # ---------------------------------------------
    print("Iniciando carga a la base de datos...")
    
    for _, row in df.iterrows():
        intentos = 0
        max_intentos = 3
        while intentos < max_intentos:
            try:
                # Creación del Paciente
                paciente = Paciente.objects.create(
                    nombres=row['nombres'],
                    apellidos=row['apellidos'],
                    sexo=row['sexo'],
                    edad=int(row['edad'])
                )
                
                # Creación del Registro Clínico (usando los nombres exactos de tu lista)
                RegistroClinico.objects.create(
                    paciente=paciente,
                    fecha_consulta=row['fecha_consulta'],
                    presion_sistolica=row['presión_sistólica'],
                    presion_diastolica=row['presión_diastólica'],
                    frecuencia_cardiaca=row['frecuencia_cardiaca'],
                    glucosa=row['glucosa'],
                    colesterol=row['colesterol'],
                    peso=row['peso'],
                    altura=row['altura'],
                    imc=row['IMC'],
                    temperatura=row['temperatura'],
                    saturacion_oxigeno=row['saturación_oxígeno'],
                    fumador=row['fumador'],
                    consumo_alcohol=row['consumo_alcohol'],
                    actividad_fisica=row['actividad_física'],
                    antecedentes_familiares=row['antecedentes_familiares'],
                    diagnostico_preliminar=row['diagnóstico_preliminar'],
                    riesgo_enfermedad=row['riesgo_enfermedad']
                )
                break # Éxito, salimos del while
            except DatabaseError:
                intentos += 1
                time.sleep(1)
    
    print("¡Proceso ETL completado con éxito!")