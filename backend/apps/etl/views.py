import os
import csv
import tempfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.analytics.decorators import role_required
from apps.etl.models import ETLLog, RegistroClinico
from .processor import run_etl


# ── API Views ────────────────────────────────────────────────────────

class EjecutarETLView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        archivo = request.FILES.get('archivo')

        if archivo:
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
                {'error': 'Archivo no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        log = ETLLog.objects.create(
            usuario=request.user,
            estado='en_proceso',
            archivo_fuente=nombre_archivo,
        )

        resultado = run_etl(ruta)

        log.registros_procesados = resultado.get('registros_procesados', 0)
        log.registros_fallidos = resultado.get('registros_fallidos', 0)
        log.tiempo_ejecucion = resultado.get('tiempo_ejecucion', 0)
        log.estado = 'exitoso' if resultado.get('exito') else 'fallido'
        log.log_detalle = resultado.get('log_detalle', '')
        log.mensaje_error = resultado.get('mensaje_error', '')
        log.save()

        if resultado.get('exito'):
            return Response({
                'mensaje': 'ETL ejecutado correctamente.',
                'registros_procesados': log.registros_procesados,
                'log_id': log.id,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'El ETL falló.',
                'detalle': log.mensaje_error,
                'log_id': log.id,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistorialETLView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = ETLLog.objects.select_related('usuario').all()[:50]
        data = [{
            'id': log.id,
            'fecha_ejecucion': log.fecha_ejecucion.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': log.usuario.username if log.usuario else 'Sistema',
            'archivo_fuente': log.archivo_fuente,
            'registros_procesados': log.registros_procesados,
            'registros_fallidos': log.registros_fallidos,
            'tiempo_ejecucion': log.tiempo_ejecucion,
            'estado': log.estado,
        } for log in logs]
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


# ── Vistas web ───────────────────────────────────────────────────────

@login_required
@role_required(allowed_roles=['Analista', 'Admin'])
def historial_web(request):
    logs = ETLLog.objects.select_related('usuario').all()
    return render(request, 'etl/historial_etl.html', {'historial': logs})


@login_required
@role_required(allowed_roles=['Analista', 'Admin', 'Médico'])
def exportar_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="pacientes_clinicos.csv"'
    response.write('\ufeff')  # BOM para Excel

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nombres', 'Apellidos', 'Edad', 'Sexo',
        'Peso', 'Altura', 'IMC', 'Presión Sistólica', 'Presión Diastólica',
        'Frecuencia Cardíaca', 'Glucosa', 'Colesterol', 'Saturación O2',
        'Temperatura', 'Fumador', 'Consumo Alcohol', 'Actividad Física',
        'Diagnóstico', 'Riesgo', 'Fecha Consulta'
    ])

    registros = RegistroClinico.objects.select_related('paciente').all()
    for r in registros:
        writer.writerow([
            r.paciente.identificacion,
            r.paciente.nombres,
            r.paciente.apellidos,
            r.paciente.edad,
            r.paciente.sexo,
            r.peso, r.altura, r.imc,
            r.presion_sistolica, r.presion_diastolica,
            r.frecuencia_cardiaca, r.glucosa, r.colesterol,
            r.saturacion_oxigeno, r.temperatura,
            'Sí' if r.fumador else 'No',
            'Sí' if r.consumo_alcohol else 'No',
            r.actividad_fisica,
            r.diagnostico_preliminar,
            r.riesgo_enfermedad,
            r.fecha_consulta,
        ])

    return response


@login_required
@role_required(allowed_roles=['Analista', 'Admin', 'Médico'])
def exportar_excel(request):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return HttpResponse("openpyxl no instalado. Corre: pip install openpyxl", status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pacientes Clínicos"

    headers = [
        'ID', 'Nombres', 'Apellidos', 'Edad', 'Sexo',
        'Peso', 'Altura', 'IMC', 'Presión Sistólica', 'Presión Diastólica',
        'Frecuencia Cardíaca', 'Glucosa', 'Colesterol', 'Saturación O2',
        'Temperatura', 'Fumador', 'Consumo Alcohol', 'Actividad Física',
        'Diagnóstico', 'Riesgo', 'Fecha Consulta'
    ]

    # Estilo encabezado
    header_fill = PatternFill(start_color="0D6EFD", end_color="0D6EFD", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Colores por riesgo
    colores = {
        'Crítico': 'FFCCCC',
        'Alto': 'FFE5CC',
        'Medio': 'FFFACC',
        'Bajo': 'CCFFCC',
    }

    registros = RegistroClinico.objects.select_related('paciente').all()
    for row_num, r in enumerate(registros, 2):
        datos = [
            r.paciente.identificacion, r.paciente.nombres, r.paciente.apellidos,
            r.paciente.edad, r.paciente.sexo,
            r.peso, r.altura, r.imc,
            r.presion_sistolica, r.presion_diastolica,
            r.frecuencia_cardiaca, r.glucosa, r.colesterol,
            r.saturacion_oxigeno, r.temperatura,
            'Sí' if r.fumador else 'No',
            'Sí' if r.consumo_alcohol else 'No',
            r.actividad_fisica, r.diagnostico_preliminar,
            r.riesgo_enfermedad, str(r.fecha_consulta),
        ]
        color = colores.get(r.riesgo_enfermedad, 'FFFFFF')
        fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

        for col, valor in enumerate(datos, 1):
            cell = ws.cell(row=row_num, column=col, value=valor)
            cell.fill = fill

    # Ajustar ancho columnas
    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 30)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="pacientes_clinicos.xlsx"'
    wb.save(response)
    return response