from django.core.exceptions import ValidationError
from django.test import TestCase, SimpleTestCase

from .models import Paciente
from .validators import normalizar_rut


class RutTests(SimpleTestCase):
    def test_formatos_equivalentes(self):
        for rut in ('12.345.678-5', '123456785', ' 12 345 678 - 5 '):
            self.assertEqual(normalizar_rut(rut), '12345678-5')

    def test_k_minuscula(self):
        self.assertEqual(normalizar_rut('1.000.005-k'), '1000005-K')

    def test_invalidos(self):
        for rut in ('', '12345678-9', 'abc', '0-0', '12x345678-5'):
            with self.subTest(rut=rut), self.assertRaises(ValidationError):
                normalizar_rut(rut)


class PacienteTests(TestCase):
    def test_modelo_normaliza_rut(self):
        p = Paciente.objects.create(rut='12.345.678-5', nombre='Paciente de prueba', edad=30, sexo='F', prevision='Fonasa')
        self.assertEqual(p.rut, '12345678-5')
