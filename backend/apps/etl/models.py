from django.db import models

class Paciente(models.Model):
    # Campos básicos del paciente (La Cédula será la Llave Primaria)
    cedula = models.CharField(max_length=20, unique=True, primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    edad = models.IntegerField()
    genero = models.CharField(max_length=20)  # Masculino, Femenino, Otro
    ciudad = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre_completo} ({self.cedula})"

class RegistroClinico(models.Model):
    # Conectamos cada registro con un Paciente específico usando una Llave Foránea
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial')
    
    # Datos médicos que se extraerán del archivo de Excel
    fecha_visita = models.DateField()
    presion_arterial = models.CharField(max_length=20)  # Ejemplo: "120/80"
    nivel_azucar = models.FloatField()                  # Glucosa en sangre
    colesterol = models.IntegerField()
    
    # Diagnóstico médico y el resultado que calculará la Inteligencia Artificial
    diagnostico = models.TextField()
    prediccion_riesgo = models.CharField(max_length=50, blank=True, null=True) # Alto, Medio, Bajo
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Registro de {self.paciente.nombre_completo} - {self.fecha_visita}"