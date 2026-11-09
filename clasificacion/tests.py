from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.management import call_command
from io import StringIO

from .models import ReglaClasificacion
from .services import MotorReconocimiento


class MotorTests(TestCase):
    def test_palabras_y_regex_en_ambos_campos(self):
        ReglaClasificacion.objects.create(nombre='Término de prueba', enfermedad='Condición ficticia A', categoria='ENO', tipo='PALABRA', patron='término alfa', prioridad=1)
        ReglaClasificacion.objects.create(nombre='Patrón de prueba', enfermedad='Condición ficticia B', categoria='GES_AUGE', tipo='REGEX', patron=r'codigo\s+B\d+', prioridad=2)
        resultado = MotorReconocimiento().clasificar('TERMINO ALFA', 'codigo B12')
        self.assertEqual(resultado['clasificacion'], 'ENO')
        self.assertEqual(len(resultado['enfermedades']), 2)
        self.assertEqual(len(resultado['reglas_aplicadas']), 2)

    def test_no_coincide_subcadena_ni_regla_inactiva(self):
        ReglaClasificacion.objects.create(nombre='A', enfermedad='A', categoria='ENO', tipo='PALABRA', patron='alfa')
        ReglaClasificacion.objects.create(nombre='B', enfermedad='B', categoria='ENO', tipo='PALABRA', patron='beta', activa=False)
        self.assertEqual(MotorReconocimiento().clasificar('alfabeto beta', '')['clasificacion'], 'SIN_ANTECEDENTES')

    def test_regex_invalida_se_rechaza(self):
        regla = ReglaClasificacion(nombre='A', enfermedad='A', categoria='ENO', tipo='REGEX', patron='[')
        with self.assertRaises(ValidationError):
            regla.full_clean()

    def test_reclasificar_historial_conserva_seguimiento(self):
        from importaciones.tests import planilla, FILA
        from importaciones.services import importar_excel
        from pacientes.models import Consulta
        fila = [*FILA]
        fila[6] = 'alfa'
        importar_excel(planilla([fila]), 'prueba.xlsx')
        salida = StringIO()
        call_command('reclasificar', stderr=salida)
        self.assertIn('No hay reglas activas', salida.getvalue())
        regla = ReglaClasificacion.objects.create(nombre='A', enfermedad='A', categoria='GES_AUGE', tipo='PALABRA', patron='alfa')
        call_command('reclasificar', stdout=StringIO())
        c = Consulta.objects.get()
        self.assertEqual(c.clasificacion, 'GES_AUGE')
        self.assertTrue(c.ges_vigente)
        c.ges_vigente = False
        c.save()
        call_command('reclasificar', stdout=StringIO())
        c.refresh_from_db()
        self.assertFalse(c.ges_vigente)
        regla.categoria = 'ENO'
        regla.save()
        call_command('reclasificar', stdout=StringIO())
        c.refresh_from_db()
        self.assertFalse(c.eno_notificado)
        self.assertEqual(c.clasificacion, 'ENO')

# Create your tests here.
