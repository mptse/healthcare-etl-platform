import os
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.etl.processor import run_etl


class Command(BaseCommand):
    help = 'Ejecuta el ETL del dataset clínico'

    def handle(self, *args, **kwargs):
        # BASE_DIR apunta a healthcare-etl-platform/ (3 niveles arriba de settings.py)
        # entonces la ruta correcta es BASE_DIR/backend/apps/etl/data/
        ruta_completa = os.path.join(
            settings.BASE_DIR, 'backend', 'apps', 'etl', 'data', 'dataset_clinico.xlsx'
        )

        self.stdout.write(f"Buscando archivo en: {ruta_completa}")

        if not os.path.exists(ruta_completa):
            self.stdout.write(self.style.ERROR(f"Archivo no encontrado: {ruta_completa}"))
            return

        if run_etl(ruta_completa):
            self.stdout.write(self.style.SUCCESS("¡Éxito! Datos cargados correctamente."))
        else:
            self.stdout.write(self.style.ERROR("Error durante el procesamiento ETL."))