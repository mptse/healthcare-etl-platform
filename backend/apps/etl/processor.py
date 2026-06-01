import pandas as pd
from apps.etl.models import Paciente # Asegúrate de que este es el nombre de tu modelo

def run_etl():
    # 1. Extracción
    file_path = 'dataset_clinico_etl_1800_registros.xlsx'
    df = pd.read_excel(file_path)

    # 2. Transformación
    # Corregir errores comunes (ejemplo: hipertensión mal escrita)
    df['diagnostico_preliminar'] = df['diagnostico_preliminar'].replace(['hipertencion', 'hipertensión'], 'Hipertensión')
    
    # Eliminar duplicados si los hubiera
    df = df.drop_duplicates()

    # 3. Carga
    for _, row in df.iterrows():
        Paciente.objects.create(
            nombres=row['nombres'],
            apellidos=row['apellidos'],
            edad=row['edad'],
            # ... (agrega aquí todos los campos de tu modelo)
            riesgo_enfermedad=row['riesgo_enfermedad'],
            fecha_consulta=row['fecha_consulta']
        )
    print("¡Carga masiva completada con éxito!")

# Para ejecutarlo, abrirías la terminal y escribirías: python manage.py shell
# Y luego: from apps.etl.processor import run_etl; run_etl()