import json

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import FieldError
from django.db import connection
from django.test import TestCase, override_settings

from .models import CambioPaciente, Consulta, Paciente


@override_settings(CLAVE_CIFRADO=Fernet.generate_key())
class CifradoBaseDatosTests(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            rut='12345678-5', nombre='Persona ficticia', edad=30,
            sexo='F', prevision='Fonasa A',
        )
        self.textos = {
            'antecedentes': 'Antecedente ficticio con tilde: presión',
            'signos_vitales': 'Signo vital ficticio de prueba',
            'enfermedades_declaradas': 'Condición ficticia de prueba',
            'ultimas_consultas': 'Control ficticio anterior',
        }
        self.consulta = Consulta.objects.create(
            paciente=self.paciente, huella='cifrado:prueba',
            nombre=self.paciente.nombre, edad=30, sexo='F',
            prevision='Fonasa A', **self.textos,
        )

    def test_textos_cifrados_en_sql_y_legibles_en_django(self):
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT antecedentes, signos_vitales, enfermedades_declaradas, '
                'ultimas_consultas FROM pacientes_consulta WHERE id = %s',
                [self.consulta.pk],
            )
            guardados = cursor.fetchone()
        self.consulta.refresh_from_db()
        for (campo, original), guardado in zip(self.textos.items(), guardados):
            with self.subTest(campo=campo):
                self.assertTrue(guardado.startswith('eno:v1:'))
                self.assertNotIn(original, guardado)
                self.assertEqual(getattr(self.consulta, campo), original)

    def test_historial_cifrado_y_recuperable(self):
        anterior = {'antecedentes': 'Texto clínico anterior', 'edad': 30}
        posterior = {'antecedentes': 'Texto clínico corregido', 'edad': 31}
        cambio = CambioPaciente.objects.create(
            paciente=self.paciente, accion='Prueba de cifrado',
            antes=anterior, despues=posterior,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT antes, despues FROM pacientes_cambiopaciente WHERE id = %s',
                [cambio.pk],
            )
            valores = cursor.fetchone()
        for valor in valores:
            self.assertTrue(json.loads(valor).startswith('eno:v1:'))
            self.assertNotIn('Texto clínico', valor)
        cambio.refresh_from_db()
        self.assertEqual(cambio.antes, anterior)
        self.assertEqual(cambio.despues, posterior)

    def test_guardar_de_nuevo_no_duplica_cifrado(self):
        self.consulta.refresh_from_db()
        self.consulta.save()
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.antecedentes, self.textos['antecedentes'])

    def test_update_cifra_el_valor_nuevo(self):
        nuevo = 'Nuevo antecedente ficticio'
        Consulta.objects.filter(pk=self.consulta.pk).update(antecedentes=nuevo)
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT antecedentes FROM pacientes_consulta WHERE id = %s',
                [self.consulta.pk],
            )
            guardado = cursor.fetchone()[0]
        self.assertTrue(guardado.startswith('eno:v1:'))
        self.assertNotIn(nuevo, guardado)
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.antecedentes, nuevo)

    def test_clave_incorrecta_impide_leer_registro(self):
        with override_settings(CLAVE_CIFRADO=Fernet.generate_key()):
            with self.assertRaises(InvalidToken):
                Consulta.objects.get(pk=self.consulta.pk)

    def test_busqueda_sobre_texto_cifrado_se_rechaza(self):
        with self.assertRaises(FieldError):
            Consulta.objects.filter(antecedentes__icontains='ficticio').exists()
