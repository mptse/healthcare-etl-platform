from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.analytics.decorators import role_required
from .trainer import entrenar_modelo, predecir_riesgo
from .models import ModeloML


# ── Vista web ────────────────────────────────────────────────────────
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
        'resultado':  resultado,
        'error':      error,
        'prediccion': prediccion,
        'historial':  historial,
    })


# ── APIs REST ────────────────────────────────────────────────────────
class EntrenarModeloAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        resultado, error = entrenar_modelo()
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado)


class PredecirAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        campos = [
            'edad', 'imc', 'glucosa', 'colesterol',
            'presion_sis', 'presion_dias', 'frecuencia',
            'saturacion', 'temperatura'
        ]
        try:
            kwargs = {c: float(request.data.get(c, 0)) for c in campos}
            kwargs['fumador']         = bool(request.data.get('fumador', False))
            kwargs['consumo_alcohol'] = bool(request.data.get('consumo_alcohol', False))
            resultado = predecir_riesgo(**kwargs)
            return Response(resultado)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistorialModelosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        modelos = ModeloML.objects.all()
        data = [{
            'id':                  m.id,
            'algoritmo':           m.algoritmo,
            'fecha_entrenamiento': m.fecha_entrenamiento.strftime('%Y-%m-%d %H:%M'),
            'accuracy':            round(m.accuracy * 100, 2),
            'precision':           round(m.precision * 100, 2),
            'recall':              round(m.recall * 100, 2),
            'f1_score':            round(m.f1_score * 100, 2),
            'total_registros':     m.total_registros,
            'activo':              m.activo,
        } for m in modelos]
        return Response({'modelos': data, 'total': len(data)})


class EstadoModeloAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        modelo_activo = ModeloML.objects.filter(activo=True).first()
        return Response({
            'entrenado': modelo_activo is not None,
            'modelo_activo': {
                'algoritmo': modelo_activo.algoritmo,
                'accuracy':  round(modelo_activo.accuracy * 100, 2),
                'fecha':     modelo_activo.fecha_entrenamiento.strftime('%Y-%m-%d %H:%M'),
            } if modelo_activo else None
        })