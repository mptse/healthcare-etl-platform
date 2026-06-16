********

## Instalación y Configuración

** 1. Clonar el repositorio

```bash
git clone https://github.com/mptse/healthcare-etl-platform.git
cd healthcare-etl-platform
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\\Scripts\activate


### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

SECRET_KEY=tu_secret_key_de_django
DEBUG=True
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_db
ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=db.tu-proyecto.supabase.co
DB_PORT=5432

### 5. Aplicar migraciones

```bash
cd backend
python manage.py migrate
```

### 6. Crear grupos y usuarios

```bash
python manage.py setup_groups
python manage.py createsuperuser
```

### 7. Cargar dataset clínico

```bash
python manage.py procesar_clinico
```

### 8. Recalcular riesgos con reglas clínicas

```bash
python manage.py shell
```

```python
from apps.ml.trainer import recalcular_riesgos_bd
recalcular_riesgos_bd()
exit()
```

### 9. Ejecutar servidor

```bash
python manage.py runserver
```

Accede en: `http://127.0.0.1:8000`

---

## Roles del Sistema

| Rol | Funcionalidades |
|-----|----------------|
| **Admin** | Gestión completa, todos los dashboards, ML, ETL, exportación |
| **Analista** | Dashboard analítico, ML, historial ETL, subida de datasets, exportación |
| **Médico** | Dashboard clínico, visualización de pacientes, filtros, exportación |

---

## Proceso ETL

El sistema ejecuta un proceso ETL completo sobre el dataset clínico:

### Extract
- Lectura de archivos Excel (.xlsx) y CSV
- Soporte para subida manual desde el dashboard
- Dataset base de 1800 registros clínicos simulados

### Transform
- Normalización de columnas (tildes, mayúsculas, espacios)
- Eliminación de duplicados por `id_paciente + fecha_consulta`
- Corrección de tipos de datos (texto a numérico)
- Normalización de sexo: M/F → Masculino/Femenino
- Normalización de diagnósticos con errores ortográficos
- Clasificación de riesgo con reglas clínicas reales:
  - **Crítico**: ≥10 puntos
  - **Alto**: 6-9 puntos
  - **Medio**: 3-5 puntos
  - **Bajo**: 0-2 puntos
- Cálculo automático de IMC

### Load
- Inserción inteligente con `get_or_create`
- Actualización de registros existentes sin duplicar
- Registro de historial de ejecuciones (ETLLog)

---

## Machine Learning

### Modelo
- **Algoritmo**: Random Forest (200 árboles)
- **Variables predictoras**: edad, IMC, glucosa, colesterol, presión sistólica, presión diastólica, frecuencia cardíaca, saturación O₂, temperatura, fumador, consumo de alcohol
- **Variable objetivo**: riesgo_enfermedad (Bajo, Medio, Alto, Crítico)

### Métricas mostradas
- Accuracy
- Precision
- Recall
- F1-Score
- Matriz de confusión
- Gráfica radar de métricas

### Predicción individual
El sistema permite ingresar los datos de un paciente y predice su nivel de riesgo en tiempo real con probabilidades por clase.

---

## APIs REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Autenticación de usuario |
| `/api/dashboard/kpis/` | GET | KPIs generales del sistema |
| `/api/dashboard/estadisticas/` | GET | Estadística descriptiva |
| `/api/dashboard/segmentacion/` | GET | Segmentación de pacientes |
| `/api/dashboard/criticos/` | GET | Pacientes críticos y alto riesgo |
| `/api/etl/run/` | POST | Ejecutar proceso ETL |
| `/api/etl/historial/` | GET | Historial de ejecuciones ETL |
| `/api/etl/historial/<id>/` | GET | Detalle de ejecución ETL |

---

## Funcionalidades por Dashboard

### Dashboard Analista
- KPIs: total pacientes, críticos, alto y bajo riesgo
- Gráfica de distribución por riesgo (doughnut)
- Gráfica de distribución por sexo (pie)
- Gráfica de grupos de edad (barras)
- Clasificación IMC (barras)
- Promedios clínicos con desviación estándar y mediana
- Tabla de estadística descriptiva completa
- Tabla de pacientes críticos y alto riesgo

### Dashboard Médico
- KPIs: pacientes críticos, hipertensos, glucosa alta, saturación baja
- Búsqueda en tiempo real por nombre/apellido
- Filtro por nivel de riesgo y rango de edad
- Tabla completa de todos los pacientes con alertas visuales
- Exportación CSV, Excel y PDF

### Dashboard Administrador
- KPIs globales: registros, pacientes, críticos, alto riesgo
- KPIs de salud poblacional: fumadores, hipertensos, diabéticos, saturación baja
- Gráfica de distribución de riesgo (barras)
- Gráfica por sexo (pie)
- Gráfica por grupos de edad (barras)
- Promedios clínicos poblacionales

### Dashboard Machine Learning
- Entrenamiento del modelo Random Forest
- Métricas del modelo (Accuracy, Precision, Recall, F1-Score)
- Matriz de confusión
- Gráfica radar de métricas
- Historial de modelos entrenados
- Predicción individual de riesgo con probabilidades

---

## Exportación de Datos

| Formato | Descripción |
|---------|-------------|
| **CSV** | Todos los registros clínicos con BOM UTF-8 para Excel |
| **Excel** | Archivo .xlsx con colores por nivel de riesgo |
| **PDF** | Reporte clínico con tabla formateada y colores por riesgo |

---

## Dataset Clínico

El dataset incluye 1850 registros brutos con:
- 1800 registros base
- 50 duplicados intencionales
- Valores nulos
- Tipos de datos incorrectos
- Valores atípicos
- Errores ortográficos en diagnósticos

Después del proceso ETL quedan **1800 registros limpios**.

### Variables del Dataset

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id_paciente | Integer | Identificador único |
| nombres | String | Nombres del paciente |
| apellidos | String | Apellidos del paciente |
| edad | Integer | Edad en años |
| sexo | String | Masculino / Femenino |
| peso | Float | Peso en kg |
| altura | Float | Altura en metros |
| imc | Float | Índice de Masa Corporal |
| presion_sistolica | Integer | Presión sistólica mmHg |
| presion_diastolica | Integer | Presión diastólica mmHg |
| frecuencia_cardiaca | Integer | Frecuencia cardíaca bpm |
| glucosa | Float | Glucosa mg/dL |
| colesterol | Integer | Colesterol mg/dL |
| saturacion_oxigeno | Float | Saturación O₂ % |
| temperatura | Float | Temperatura °C |
| antecedentes_familiares | Boolean | Antecedentes familiares |
| fumador | Boolean | Fumador activo |
| consumo_alcohol | Boolean | Consumo de alcohol |
| actividad_fisica | String | Nivel de actividad física |
| diagnostico_preliminar | String | Diagnóstico preliminar |
| riesgo_enfermedad | String | Bajo/Medio/Alto/Crítico |
| fecha_consulta | Date | Fecha de la consulta |

---

## Dependencias Principales
