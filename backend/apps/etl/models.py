from django.db import models
from django.conf import settings  


class Paciente(models.Model):
    identificacion = models.CharField(max_length=50, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.identificacion})"


class RegistroClinico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial')
    peso = models.FloatField()
    altura = models.FloatField()
    imc = models.FloatField()
    presion_sistolica = models.IntegerField()
    presion_diastolica = models.IntegerField()
    frecuencia_cardiaca = models.IntegerField()
    glucosa = models.FloatField()
    colesterol = models.IntegerField()
    saturacion_oxigeno = models.FloatField()
    temperatura = models.FloatField()
    antecedentes_familiares = models.TextField()
    fumador = models.BooleanField()
    consumo_alcohol = models.BooleanField()
    actividad_fisica = models.CharField(max_length=50)
    diagnostico_preliminar = models.TextField()
    riesgo_enfermedad = models.CharField(max_length=50)
    fecha_consulta = models.DateField()

    def __str__(self):
        return f"Registro: {self.paciente.nombres} - {self.fecha_consulta}"


class ETLLog(models.Model):
    ESTADO_CHOICES = [
        ('exitoso', 'Exitoso'),
        ('fallido', 'Fallido'),
        ('en_proceso', 'En Proceso'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← esta es la corrección clave
        on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)
    registros_procesados = models.IntegerField(default=0)
    registros_fallidos = models.IntegerField(default=0)
    tiempo_ejecucion = models.FloatField(default=0.0, help_text="Segundos")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_proceso')
    archivo_fuente = models.CharField(max_length=255, blank=True)
    mensaje_error = models.TextField(blank=True)
    log_detalle = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_ejecucion']
        verbose_name = 'Log ETL'
        verbose_name_plural = 'Logs ETL'

    def __str__(self):
        return f"ETL {self.fecha_ejecucion.strftime('%Y-%m-%d %H:%M')} — {self.estado}"