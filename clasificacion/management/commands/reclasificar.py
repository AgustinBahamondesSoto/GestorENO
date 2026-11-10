from django.core.management.base import BaseCommand
from django.db import transaction
from clasificacion.services import MotorReconocimiento, reclasificar_historial


class Command(BaseCommand):
    help = 'Reaplica el diccionario activo al historial y conserva los estados de seguimiento existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        motor = MotorReconocimiento()
        if not motor.reglas:
            self.stderr.write('No hay reglas activas. Los resultados anteriores se actualizarán a Sin coincidencias.')
        cantidad = reclasificar_historial()
        self.stdout.write(self.style.SUCCESS(f'Consultas reclasificadas: {cantidad}'))
