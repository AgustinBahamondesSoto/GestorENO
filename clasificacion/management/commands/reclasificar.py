from django.core.management.base import BaseCommand
from django.db import transaction
from clasificacion.services import MotorReconocimiento
from pacientes.models import Consulta


class Command(BaseCommand):
    help = 'Reaplica el diccionario activo al historial y conserva los estados de seguimiento existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        motor = MotorReconocimiento()
        if not motor.reglas:
            self.stderr.write('No hay reglas activas. No se modificaron las consultas.')
            return
        cantidad = 0
        for consulta in Consulta.objects.iterator():
            resultado = motor.clasificar(consulta.antecedentes, consulta.signos_vitales, consulta.enfermedades_declaradas)
            if resultado['clasificacion'] == 'GES_AUGE' and consulta.clasificacion != 'GES_AUGE':
                consulta.ges_vigente = True
            if resultado['clasificacion'] == 'ENO' and consulta.clasificacion != 'ENO':
                consulta.eno_notificado = False
            for campo, valor in resultado.items():
                setattr(consulta, campo, valor)
            consulta.save(update_fields=[*resultado.keys(), 'ges_vigente', 'eno_notificado'])
            cantidad += 1
        self.stdout.write(self.style.SUCCESS(f'Consultas reclasificadas: {cantidad}'))
