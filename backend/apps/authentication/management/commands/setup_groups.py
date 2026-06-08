from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
# CAMBIA ESTA LÍNEA:
from django.contrib.auth import get_user_model 

User = get_user_model() # Esto obtiene automáticamente tu usuario personalizado

class Command(BaseCommand):
    help = 'Crea grupos y un usuario de prueba automáticamente'

    def handle(self, *args, **kwargs):
        # 1. Crear Grupos
        roles = ['Analista', 'Médico', 'Admin']
        for role in roles:
            Group.objects.get_or_create(name=role)
            self.stdout.write(f'Grupo {role} creado o verificado.')

        # 2. Crear usuario de prueba
        username = 'analista_test'
        password = 'password123'
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, password=password)
            grupo = Group.objects.get(name='Analista')
            user.groups.add(grupo)
            self.stdout.write(f'Usuario {username} creado y asignado a Analista.')
        else:
            self.stdout.write(f'El usuario {username} ya existe.')