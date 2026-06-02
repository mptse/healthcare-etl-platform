from pathlib import Path
import pandas as pd
from apps.etl.models import Paciente, RegistroClinico

COLUMN_NORMALIZATION = {
    'á': 'a',
    'é': 'e',
    'í': 'i',
    'ó': 'o',
    'ú': 'u',
    'ñ': 'n',
    'ü': 'u',
}


def normalize_column_name(name: str) -> str:
    if not isinstance(name, str):
        return str(name)
    normalized = name.strip().lower()
    for accented, unaccented in COLUMN_NORMALIZATION.items():
        normalized = normalized.replace(accented, unaccented)
    normalized = normalized.replace(' ', '_').replace('-', '_')
    return normalized


def safe_int(value, default=0):
    if pd.isna(value):
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value):
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {'si', 'sí', 'true', '1', 'yes', 'y'}


def safe_text(value, default='sin dato'):
    if pd.isna(value):
        return default
    return str(value).strip().lower()


def safe_date(value, default=None):
    if pd.isna(value):
        return default
    try:
        date_value = pd.to_datetime(value, errors='coerce')
        return date_value.date() if not pd.isna(date_value) else default
    except Exception:
        return default


def run_etl(file_path: str | Path | None = None):
    if file_path is None:
        file_path = Path(__file__).resolve().parent.parent / 'dataset_clinico_etl_1800_registros.xlsx'
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {file_path}")

    df = pd.read_excel(file_path)
    df = df.drop_duplicates()
    df.columns = [normalize_column_name(col) for col in df.columns]

    required_columns = {
        'nombres', 'apellidos', 'sexo', 'edad', 'fecha_consulta',
        'presion_sistolica', 'presion_diastolica', 'frecuencia_cardiaca',
        'glucosa', 'colesterol', 'peso', 'altura', 'imc', 'temperatura',
        'saturacion_oxigeno', 'fumador', 'consumo_alcohol', 'actividad_fisica',
        'antecedentes_familiares', 'diagnostico_preliminar', 'riesgo_enfermedad'
    }

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el archivo Excel: {sorted(missing)}")

    for col in df.columns:
        if df[col].dtype.kind in 'biufc':
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna('sin dato')

    print('Iniciando carga de datos...')

    for _, row in df.iterrows():
        paciente = Paciente.objects.create(
            nombres=safe_text(row['nombres']),
            apellidos=safe_text(row['apellidos']),
            sexo=safe_text(row['sexo']),
            edad=safe_int(row['edad'])
        )

        RegistroClinico.objects.create(
            paciente=paciente,
            fecha_consulta=safe_date(row['fecha_consulta']),
            presion_sistolica=safe_int(row['presion_sistolica']),
            presion_diastolica=safe_int(row['presion_diastolica']),
            frecuencia_cardiaca=safe_int(row['frecuencia_cardiaca']),
            glucosa=safe_float(row['glucosa']),
            colesterol=safe_int(row['colesterol']),
            peso=safe_float(row['peso']),
            altura=safe_float(row['altura']),
            imc=safe_float(row['imc']),
            temperatura=safe_float(row['temperatura']),
            saturacion_oxigeno=safe_float(row['saturacion_oxigeno']),
            fumador=safe_bool(row['fumador']),
            consumo_alcohol=safe_bool(row['consumo_alcohol']),
            actividad_fisica=safe_text(row['actividad_fisica']),
            antecedentes_familiares=safe_text(row['antecedentes_familiares']),
            diagnostico_preliminar=safe_text(row['diagnostico_preliminar']),
            riesgo_enfermedad=safe_text(row['riesgo_enfermedad'])
        )

    print('¡ÉXITO: Proceso ETL completado con éxito!')
