from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model 

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea grupos y usuarios de prueba automáticamente'

    def handle(self, *args, **kwargs):
        # 1. Crear Grupos
        roles = ['Analista', 'Médico', 'Admin']
        for role in roles:
            Group.objects.get_or_create(name=role)
            self.stdout.write(f'Grupo {role} verificado.')

        # 2. Lista de usuarios a crear con sus respectivos roles
        usuarios_a_crear = [
            {'username': 'analista_test', 'password': 'password123', 'rol': 'Analista'},
            {'username': 'medico_test', 'password': 'password123', 'rol': 'Médico'},
            {'username': 'admin_test', 'password': 'password123', 'rol': 'Admin'},
        ]

        # 3. Ciclo para procesar cada usuario
        for data in usuarios_a_crear:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(username=data['username'], password=data['password'])
                
                # Asignar al grupo correspondiente
                grupo = Group.objects.get(name=data['rol'])
                user.groups.add(grupo)
                
                # Si es Admin, darle permisos de superusuario
                if data['rol'] == 'Admin':
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                
                self.stdout.write(f'Usuario {data["username"]} creado y asignado a {data["rol"]}.')
            else:
                self.stdout.write(f'El usuario {data["username"]} ya existe.')