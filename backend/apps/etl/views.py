import os
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .processor import run_etl
from .models import ETLLog


class EjecutarETLView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Permite subir un archivo o usar el dataset por defecto
        archivo = request.FILES.get('archivo')

        if archivo:
            import tempfile
            sufijo = '.xlsx' if archivo.name.endswith('.xlsx') else '.csv'
            with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
                for chunk in archivo.chunks():
                    tmp.write(chunk)
                ruta = tmp.name
            nombre_archivo = archivo.name
        else:
            ruta = os.path.join(
                settings.BASE_DIR, 'backend', 'apps', 'etl', 'data', 'dataset_clinico.xlsx'
            )
            nombre_archivo = 'dataset_clinico.xlsx'

        if not os.path.exists(ruta):
            return Response(
                {'error': 'Archivo no encontrado. Sube un archivo o coloca el dataset por defecto.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear log en estado "en_proceso"
        log = ETLLog.objects.create(
            usuario=request.user,
            estado='en_proceso',
            archivo_fuente=nombre_archivo,
        )

        resultado = run_etl(ruta)

        # Actualizar log con resultado
        log.registros_procesados = resultado['registros_procesados']
        log.registros_fallidos = resultado['registros_fallidos']
        log.tiempo_ejecucion = resultado['tiempo_ejecucion']
        log.estado = 'exitoso' if resultado['exito'] else 'fallido'
        log.log_detalle = resultado['log_detalle']
        log.mensaje_error = resultado['mensaje_error']
        log.save()

        if resultado['exito']:
            return Response({
                'mensaje': 'ETL ejecutado correctamente.',
                'registros_procesados': resultado['registros_procesados'],
                'registros_fallidos': resultado['registros_fallidos'],
                'tiempo_ejecucion': resultado['tiempo_ejecucion'],
                'log_id': log.id,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'El ETL falló.',
                'detalle': resultado['mensaje_error'],
                'log_id': log.id,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistorialETLView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = ETLLog.objects.select_related('usuario').all()[:50]
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'fecha_ejecucion': log.fecha_ejecucion.strftime('%Y-%m-%d %H:%M:%S'),
                'usuario': log.usuario.username if log.usuario else 'Sistema',
                'archivo_fuente': log.archivo_fuente,
                'registros_procesados': log.registros_procesados,
                'registros_fallidos': log.registros_fallidos,
                'tiempo_ejecucion': log.tiempo_ejecucion,
                'estado': log.estado,
            })
        return Response({'historial': data, 'total': len(data)})


class DetalleETLView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            log = ETLLog.objects.get(pk=pk)
        except ETLLog.DoesNotExist:
            return Response({'error': 'Log no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': log.id,
            'fecha_ejecucion': log.fecha_ejecucion.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': log.usuario.username if log.usuario else 'Sistema',
            'archivo_fuente': log.archivo_fuente,
            'registros_procesados': log.registros_procesados,
            'registros_fallidos': log.registros_fallidos,
            'tiempo_ejecucion': log.tiempo_ejecucion,
            'estado': log.estado,
            'log_detalle': log.log_detalle,
            'mensaje_error': log.mensaje_error,
        })