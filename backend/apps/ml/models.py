from django.db import models

class ModeloML(models.Model):
    fecha_entrenamiento = models.DateTimeField(auto_now_add=True)
    algoritmo = models.CharField(max_length=100)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    total_registros = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_entrenamiento']

    def __str__(self):
        return f"{self.algoritmo} - {self.fecha_entrenamiento.strftime('%d/%m/%Y')} - Accuracy: {self.accuracy:.2%}"