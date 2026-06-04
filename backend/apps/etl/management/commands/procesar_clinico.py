import os
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.etl.processor import run_etl

class Command(BaseCommand):
    help = 'Ejecuta el ETL'

    def handle(self, *args, **kwargs):
        # settings.BASE_DIR apunta a 'backend/'. 
        # Si el archivo está ahí, solo concatenamos el nombre del archivo.
        ruta_completa = os.path.join(settings.BASE_DIR,'backend','apps','etl', 'data', 'dataset_clinico.xlsx')
        
        self.stdout.write(f"Buscando archivo en: {ruta_completa}")
        
        if os.path.exists(ruta_completa):
            if run_etl(ruta_completa):
                self.stdout.write(self.style.SUCCESS("¡Éxito! Datos cargados."))
            else:
                self.stdout.write(self.style.ERROR("Error en el procesamiento."))
        else:
            self.stdout.write(self.style.ERROR("Archivo no encontrado. Asegúrate de que esté dentro de la carpeta 'backend/data/'"))
            