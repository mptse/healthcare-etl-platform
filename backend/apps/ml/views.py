from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.analytics.decorators import role_required
from .trainer import entrenar_modelo, predecir_riesgo
from .models import ModeloML


@login_required
@role_required(allowed_roles=['Analista', 'Admin'])
def ml_dashboard(request):
    resultado = None
    error = None
    prediccion = None
    historial = ModeloML.objects.all()[:5]

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'entrenar':
            resultado, error = entrenar_modelo()

        elif accion == 'predecir':
            try:
                prediccion = predecir_riesgo(
                    edad=float(request.POST.get('edad', 0)),
                    imc=float(request.POST.get('imc', 0)),
                    glucosa=float(request.POST.get('glucosa', 0)),
                    colesterol=float(request.POST.get('colesterol', 0)),
                    presion_sis=float(request.POST.get('presion_sis', 0)),
                    presion_dias=float(request.POST.get('presion_dias', 0)),
                    frecuencia=float(request.POST.get('frecuencia', 0)),
                    saturacion=float(request.POST.get('saturacion', 0)),
                    temperatura=float(request.POST.get('temperatura', 0)),
                    fumador=request.POST.get('fumador') == 'on',
                    consumo_alcohol=request.POST.get('consumo_alcohol') == 'on',
                )
            except Exception as e:
                error = f"Error en predicción: {e}"

    return render(request, 'ml/ml_dashboard.html', {
        'resultado': resultado,
        'error': error,
        'prediccion': prediccion,
        'historial': historial,
    })