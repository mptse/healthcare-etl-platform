from django.db import models

class Paciente(models.Model):
    # Usaremos un ID automático de Django para simplificar, 
    # pero si tienes una cédula en el Excel, podemos ajustarlo después.
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class RegistroClinico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historial')
    
    # Datos médicos del Excel
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