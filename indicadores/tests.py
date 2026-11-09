from django.test import TestCase
from importaciones.tests import planilla, FILA
from importaciones.services import importar_excel
from clasificacion.models import ReglaClasificacion
from .services import calcular_indicadores
from .forms import FiltrosForm
from pacientes.models import Paciente
from django.contrib.auth import get_user_model
from io import BytesIO
from openpyxl import load_workbook


class IndicadoresTests(TestCase):
    def test_cuenta_pacientes_no_filas_y_filtra(self):
        ReglaClasificacion.objects.create(nombre='Prueba', enfermedad='Condición ficticia', categoria='ENO', tipo='PALABRA', patron='alfa')
        fila = [*FILA]
        fila[6] = 'alfa'
        otra = [*fila]
        otra[8] = '2026-10-02'
        segundo = [*FILA]
        segundo[1], segundo[2], segundo[4] = '1.000.005-K', 60, 'M'
        importar_excel(planilla([fila, otra, segundo]), 'prueba.xlsx')
        datos = calcular_indicadores()
        self.assertEqual(datos['total'], 2)
        self.assertEqual(datos['enfermedades'][0]['cantidad'], 1)
        self.assertEqual(datos['enfermedades'][0]['porcentaje'], 50)
        self.assertEqual(calcular_indicadores({'categoria': 'ENO'})['total'], 1)
        self.assertEqual(calcular_indicadores({'edad_min': 50})['total'], 1)
        self.assertEqual(calcular_indicadores({'sexo': 'F'})['total'], 1)
        self.assertEqual(calcular_indicadores({'prevision': 'ninguna'})['total'], 0)

    def test_sin_pacientes(self):
        self.assertEqual(calcular_indicadores()['total'], 0)

    def test_rango_de_edad_invertido(self):
        self.assertFalse(FiltrosForm({'edad_min': 60, 'edad_max': 20}).is_valid())

class FiltrosSeleccionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for rut, sexo, prevision in [
            ('12345678-5', 'F', 'Fonasa A'),
            ('1000005-K', 'M', 'Isapre'),
            ('11111111-1', 'F', 'fonasa a'),
        ]:
            Paciente.objects.create(
                rut=rut, nombre='Paciente ficticio', edad=30,
                sexo=sexo, prevision=prevision,
            )
        cls.usuario = get_user_model().objects.create_user(username='filtros')

    def test_opciones_reales_sin_duplicados_de_mayusculas(self):
        form = FiltrosForm()
        self.assertEqual(list(form.fields['sexo'].choices), [('', 'Todos'), ('F', 'Femenino'), ('M', 'Masculino')])
        self.assertEqual(list(form.fields['prevision'].choices), [('', 'Todas'), ('Fonasa A', 'Fonasa A'), ('Isapre', 'Isapre')])

    def test_seleccion_filtra_panel_y_excel_y_se_conserva(self):
        self.client.force_login(self.usuario)
        filtros = {'sexo': 'F', 'prevision': 'Fonasa A'}
        respuesta = self.client.get('/', filtros)
        self.assertEqual(respuesta.context['datos']['total'], 2)
        self.assertContains(respuesta, '<select name="sexo"', html=False)
        self.assertContains(respuesta, '<select name="prevision"', html=False)
        self.assertContains(respuesta, '<option value="F" selected>Femenino</option>', html=True)
        self.assertContains(respuesta, '<option value="Fonasa A" selected>Fonasa A</option>', html=True)
        excel = self.client.get('/reportes/excel/', filtros)
        self.assertEqual(excel.status_code, 200)
        libro = load_workbook(BytesIO(excel.content))
        self.assertEqual(libro['Resumen']['B2'].value, 2)

    def test_todos_y_valor_ajeno_a_las_opciones(self):
        self.assertTrue(FiltrosForm({'sexo': '', 'prevision': ''}).is_valid())
        self.assertFalse(FiltrosForm({'sexo': 'Texto cualquiera'}).is_valid())

    def test_sin_pacientes_se_puede_consultar_sin_filtros(self):
        Paciente.objects.all().delete()
        form = FiltrosForm({})
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.fields['sexo'].choices), [('', 'Todos')])
        self.assertEqual(list(form.fields['prevision'].choices), [('', 'Todas')])
