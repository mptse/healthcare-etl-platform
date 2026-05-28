from django.contrib.auth.models import AbstractUser
from django.db import models

class UsuarioPersonalizado(AbstractUser):
    # Definimos los roles que exige el reto técnico
    ROLES_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('MEDICO', 'Médico'),
        ('ANALISTA', 'Analista de Datos'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLES_CHOICES, default='MEDICO')
    especialidad = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
