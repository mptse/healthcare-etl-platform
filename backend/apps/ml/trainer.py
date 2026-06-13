import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from apps.etl.models import RegistroClinico
from .models import ModeloML


def calcular_riesgo_clinico(edad, imc, glucosa, colesterol, presion_sis,
                             presion_dias, saturacion, fumador, consumo_alcohol):
    """
    Calcula el riesgo basado en reglas clínicas reales.
    Retorna: 'Crítico', 'Alto', 'Medio', 'Bajo'
    """
    puntos = 0

    # Presión sistólica
    if presion_sis >= 180:
        puntos += 4
    elif presion_sis >= 160:
        puntos += 3
    elif presion_sis >= 140:
        puntos += 2
    elif presion_sis >= 130:
        puntos += 1

    # Glucosa
    if glucosa >= 300:
        puntos += 4
    elif glucosa >= 200:
        puntos += 3
    elif glucosa >= 126:
        puntos += 2
    elif glucosa >= 100:
        puntos += 1

    # Saturación O₂
    if saturacion < 85:
        puntos += 4
    elif saturacion < 90:
        puntos += 3
    elif saturacion < 94:
        puntos += 1

    # IMC
    if imc >= 40:
        puntos += 3
    elif imc >= 35:
        puntos += 2
    elif imc >= 30:
        puntos += 1
    elif imc < 18.5:
        puntos += 1

    # Colesterol
    if colesterol >= 280:
        puntos += 2
    elif colesterol >= 240:
        puntos += 1

    # Edad
    if edad >= 70:
        puntos += 2
    elif edad >= 55:
        puntos += 1

    # Factores de riesgo
    if fumador:
        puntos += 2
    if consumo_alcohol:
        puntos += 1

    # Clasificación
    if puntos >= 10:
        return 'Crítico'
    elif puntos >= 6:
        return 'Alto'
    elif puntos >= 3:
        return 'Medio'
    else:
        return 'Bajo'


def recalcular_riesgos_bd():
    """Recalcula y actualiza el riesgo de todos los registros en BD."""
    registros = RegistroClinico.objects.select_related('paciente').all()
    actualizados = 0

    for r in registros:
        nuevo_riesgo = calcular_riesgo_clinico(
            edad=r.paciente.edad,
            imc=r.imc,
            glucosa=r.glucosa,
            colesterol=r.colesterol,
            presion_sis=r.presion_sistolica,
            presion_dias=r.presion_diastolica,
            saturacion=r.saturacion_oxigeno,
            fumador=r.fumador,
            consumo_alcohol=r.consumo_alcohol,
        )
        if r.riesgo_enfermedad != nuevo_riesgo:
            r.riesgo_enfermedad = nuevo_riesgo
            r.save(update_fields=['riesgo_enfermedad'])
            actualizados += 1

    print(f"Riesgos actualizados: {actualizados} de {registros.count()}")
    return actualizados


def entrenar_modelo():
    registros = RegistroClinico.objects.select_related('paciente').values(
        'paciente__edad', 'imc', 'glucosa', 'colesterol',
        'presion_sistolica', 'presion_diastolica', 'frecuencia_cardiaca',
        'saturacion_oxigeno', 'temperatura', 'fumador',
        'consumo_alcohol', 'riesgo_enfermedad',
    )

    if len(registros) < 50:
        return None, "No hay suficientes datos para entrenar el modelo."

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
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )

    modelo = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced'
    )
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    ModeloML.objects.all().update(activo=False)

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

    modelo = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced'
    )
    modelo.fit(np.array(X), y_encoded)

    # Calcular riesgo esperado con reglas clínicas
    riesgo_esperado = calcular_riesgo_clinico(
        edad=edad, imc=imc, glucosa=glucosa, colesterol=colesterol,
        presion_sis=presion_sis, presion_dias=presion_dias,
        saturacion=saturacion, fumador=fumador, consumo_alcohol=consumo_alcohol
    )

    entrada = np.array([[edad, imc, glucosa, colesterol, presion_sis,
                         presion_dias, frecuencia, saturacion, temperatura,
                         1 if fumador else 0, 1 if consumo_alcohol else 0]])

    pred = modelo.predict(entrada)[0]
    proba = modelo.predict_proba(entrada)[0]

    return {
        'riesgo': le.inverse_transform([pred])[0],
        'riesgo_clinico': riesgo_esperado,
        'probabilidades': {
            clase: round(float(prob) * 100, 1)
            for clase, prob in zip(le.classes_, proba)
        }
    }