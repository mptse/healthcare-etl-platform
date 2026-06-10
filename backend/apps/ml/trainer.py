import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from apps.etl.models import RegistroClinico
from .models import ModeloML


def entrenar_modelo():
    # 1. Obtener datos
    registros = RegistroClinico.objects.select_related('paciente').values(
        'paciente__edad',
        'imc',
        'glucosa',
        'colesterol',
        'presion_sistolica',
        'presion_diastolica',
        'frecuencia_cardiaca',
        'saturacion_oxigeno',
        'temperatura',
        'fumador',
        'consumo_alcohol',
        'riesgo_enfermedad',
    )

    if len(registros) < 50:
        return None, "No hay suficientes datos para entrenar el modelo."

    # 2. Preparar features y target
    X, y = [], []
    for r in registros:
        X.append([
            r['paciente__edad'] or 0,
            r['imc'] or 0,
            r['glucosa'] or 0,
            r['colesterol'] or 0,
            r['presion_sistolica'] or 0,
            r['presion_diastolica'] or 0,
            r['frecuencia_cardiaca'] or 0,
            r['saturacion_oxigeno'] or 0,
            r['temperatura'] or 0,
            1 if r['fumador'] else 0,
            1 if r['consumo_alcohol'] else 0,
        ])
        y.append(r['riesgo_enfermedad'])

    X = np.array(X)

    # 3. Encodear target
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # 4. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )

    # 5. Entrenar Random Forest
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)

    # 6. Evaluar
    y_pred = modelo.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    # 7. Desactivar modelos anteriores
    ModeloML.objects.all().update(activo=False)

    # 8. Guardar resultado en BD
    resultado = ModeloML.objects.create(
        algoritmo='Random Forest',
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1_score=f1,
        total_registros=len(X),
        activo=True,
    )

    return {
        'modelo_id': resultado.id,
        'algoritmo': 'Random Forest',
        'accuracy': round(acc * 100, 2),
        'precision': round(prec * 100, 2),
        'recall': round(rec * 100, 2),
        'f1_score': round(f1 * 100, 2),
        'total_registros': len(X),
        'clases': list(le.classes_),
        'matriz_confusion': cm.tolist(),
    }, None


def predecir_riesgo(edad, imc, glucosa, colesterol, presion_sis,
                    presion_dias, frecuencia, saturacion, temperatura,
                    fumador, consumo_alcohol):
    registros = RegistroClinico.objects.select_related('paciente').values(
        'paciente__edad', 'imc', 'glucosa', 'colesterol',
        'presion_sistolica', 'presion_diastolica', 'frecuencia_cardiaca',
        'saturacion_oxigeno', 'temperatura', 'fumador',
        'consumo_alcohol', 'riesgo_enfermedad',
    )

    X, y = [], []
    for r in registros:
        X.append([
            r['paciente__edad'] or 0, r['imc'] or 0, r['glucosa'] or 0,
            r['colesterol'] or 0, r['presion_sistolica'] or 0,
            r['presion_diastolica'] or 0, r['frecuencia_cardiaca'] or 0,
            r['saturacion_oxigeno'] or 0, r['temperatura'] or 0,
            1 if r['fumador'] else 0, 1 if r['consumo_alcohol'] else 0,
        ])
        y.append(r['riesgo_enfermedad'])

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(np.array(X), y_encoded)

    entrada = np.array([[edad, imc, glucosa, colesterol, presion_sis,
                         presion_dias, frecuencia, saturacion, temperatura,
                         1 if fumador else 0, 1 if consumo_alcohol else 0]])

    pred = modelo.predict(entrada)[0]
    proba = modelo.predict_proba(entrada)[0]

    return {
        'riesgo': le.inverse_transform([pred])[0],
        'probabilidades': {
            clase: round(float(prob) * 100, 1)
            for clase, prob in zip(le.classes_, proba)
        }
    }