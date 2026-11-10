from io import BytesIO
from django.contrib.auth import get_user_model
from django.test import TestCase
from openpyxl import load_workbook
from importaciones.services import importar_excel
from importaciones.tests import planilla, FILA
from clasificacion.catalogo import registrar_enfermedad
from clasificacion.models import ReglaClasificacion
from pacientes.models import Paciente
from pacientes.services import registrar_consulta
from .services import calcular_indicadores, resultados_pacientes


class FiltroEnfermedadesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username='indicadores')
        self.client.force_login(self.usuario)
        self.alfa = registrar_enfermedad('Condición ficticia alfa')
        self.beta = registrar_enfermedad('Condición ficticia beta')
        ReglaClasificacion.objects.create(nombre='Alfa', enfermedad=self.alfa.nombre, categoria='ENO', tipo='PALABRA', patron=self.alfa.nombre)
        ReglaClasificacion.objects.create(nombre='Beta', enfermedad=self.beta.nombre, categoria='GES_AUGE', tipo='PALABRA', patron=self.beta.nombre)
        self.paciente = Paciente.objects.create(rut='12345678-5', nombre='Persona filtrada', edad=30, sexo='F', prevision='Fonasa A')
        for enfermedad in (self.alfa, self.beta):
            registrar_consulta(self.paciente, {'fecha': '2026-11-10', 'enfermedades': [enfermedad]}, self.usuario)

    def test_enfermedad_y_categoria_deben_coincidir_en_misma_atencion(self):
        self.assertEqual(calcular_indicadores({'enfermedad': self.alfa, 'categoria': 'GES_AUGE'})['total'], 0)
        self.assertEqual(calcular_indicadores({'enfermedad': self.alfa, 'categoria': 'ENO'})['total'], 1)

    def test_resultados_y_excel_muestran_identidad_y_clasificacion_filtrada(self):
        filtros = {'enfermedad': self.alfa.pk}
        respuesta = self.client.get('/', filtros)
        self.assertContains(respuesta, 'Persona filtrada')
        self.assertContains(respuesta, '12345678-5')
        filas = list(resultados_pacientes({'enfermedad': self.alfa}))
        self.assertEqual(filas[0]['clasificaciones'], ['ENO'])
        self.assertEqual(filas[0]['enfermedades'], [self.alfa.nombre])
        excel = self.client.get('/reportes/excel/', filtros)
        self.assertEqual(excel.status_code, 200)
        libro = load_workbook(BytesIO(excel.content))
        self.assertEqual(libro['Pacientes filtrados']['A2'].value, '12345678-5')
        self.assertEqual(libro['Pacientes filtrados']['D2'].value, 'ENO')
        self.assertEqual(libro['GES vigentes'].max_row, 1)

    def test_paciente_unico_con_varias_atenciones(self):
        registrar_consulta(self.paciente, {'fecha': '2026-11-11', 'enfermedades': [self.alfa]}, self.usuario)
        datos = calcular_indicadores({'enfermedad': self.alfa})
        self.assertEqual(datos['total'], 1)
        self.assertEqual(datos['enfermedades'][0]['cantidad'], 1)

    def test_enfermedad_sin_regla_tambien_puede_filtrarse(self):
        nueva = registrar_enfermedad('Condición sin regla')
        registrar_consulta(self.paciente, {'fecha': '2026-11-12', 'enfermedades': [nueva]}, self.usuario)
        datos = calcular_indicadores({'enfermedad': nueva})
        self.assertEqual(datos['total'], 1)
        self.assertEqual(datos['categorias'][0]['nombre'], 'Sin coincidencias')

    def test_enfermedad_inexistente_rechazada(self):
        self.assertEqual(self.client.get('/reportes/excel/', {'enfermedad': 99999}).status_code, 400)
