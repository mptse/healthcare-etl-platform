import pandas as pd
import numpy as np
from apps.etl.models import Paciente, RegistroClinico

def run_etl():
    # 1. Extracción
    file_path = 'dataset_clinico_etl_1800_registros (1).xlsx'
    df = pd.read_excel(file_path)

    # 2. Transformación
    df = df.drop_duplicates()
    
    # Manejo de Nulos
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].mean())
    
    # Normalización de diagnóstico (ajustado a la tilde real)
    df['diagnóstico_preliminar'] = df['diagnóstico_preliminar'].replace(
        ['hipertencion', 'hipertension', 'hipertensión'], 'Hipertensión'
    )

    # Cálculo de IMC
    df['IMC'] = df['peso'] / (df['altura'] ** 2)

    # 3. Carga
    for _, row in df.iterrows():
        paciente = Paciente.objects.create(
            nombres=row['nombres'],
            apellidos=row['apellidos'],
            sexo=row['sexo']
        )
        
        RegistroClinico.objects.create(
            paciente=paciente,
            fecha_consulta=row['fecha_consulta'],
            presion_sistolica=row['presión_sistólica'],
            presion_diastolica=row['presión_diastólica'],
            frecuencia_cardiaca=row['frecuencia_cardiaca'],
            glucosa=row['glucosa'],
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
    
    print("¡Proceso ETL completado con éxito!")