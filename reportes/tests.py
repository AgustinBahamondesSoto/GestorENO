from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from openpyxl import load_workbook

from clasificacion.models import ReglaClasificacion
from importaciones.tests import planilla, FILA
from importaciones.services import importar_excel
from pacientes.models import Paciente, Consulta
from .services import generar_reporte, generar_plantilla


class ReportesTests(TestCase):
    def test_excel_agrupa_y_respeta_seguimiento(self):
        ReglaClasificacion.objects.create(nombre='A', enfermedad='Prueba A', categoria='ENO', tipo='PALABRA', patron='alfa')
        ReglaClasificacion.objects.create(nombre='B', enfermedad='Prueba B', categoria='GES_AUGE', tipo='PALABRA', patron='beta')
        fila = [*FILA]
        fila[0], fila[6] = '=1+1', 'alfa'
        otra = [*fila]
        otra[8] = '2026-10-02'
        ges = [*FILA]
        ges[1], ges[6] = '1000005-K', 'beta'
        importar_excel(planilla([fila, otra, ges]), 'prueba.xlsx')
        libro = load_workbook(BytesIO(generar_reporte()))
        self.assertEqual(libro['ENO pendientes'].max_row, 2)
        self.assertEqual(libro['ENO pendientes']['B2'].value, "'=1+1")
        self.assertEqual(libro['ENO pendientes']['F2'].value, 2)
        self.assertEqual(libro['GES vigentes'].max_row, 2)
        Consulta.objects.filter(clasificacion='ENO').update(eno_notificado=True)
        Consulta.objects.filter(clasificacion='GES_AUGE').update(ges_vigente=False)
        cerrado = load_workbook(BytesIO(generar_reporte()))
        self.assertEqual(cerrado['ENO pendientes'].max_row, 1)
        self.assertEqual(cerrado['GES vigentes'].max_row, 1)

    def test_plantilla_descargable(self):
        libro = load_workbook(BytesIO(generar_plantilla()))
        self.assertEqual(libro.active['C1'].value, 'RUT')
        self.assertEqual(libro.active.max_column, 14)


class FlujoWebTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username='prueba', password='Clave-solo-pruebas-123')

    def test_rutas_protegidas(self):
        for ruta in ['/', '/pacientes/', '/importaciones/', '/reportes/excel/', '/reportes/plantilla/']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 302)

    def test_carga_historial_indicadores_exportacion(self):
        self.client.force_login(self.usuario)
        archivo = SimpleUploadedFile('prueba.xlsx', planilla([FILA]).getvalue())
        respuesta = self.client.post('/importaciones/', {'archivo': archivo})
        self.assertEqual(respuesta.status_code, 302)
        self.assertContains(self.client.get(respuesta.url), 'Consultas nuevas')
        for ruta in ['/', '/pacientes/', f'/pacientes/{Paciente.objects.get().pk}/', '/reportes/excel/', '/reportes/plantilla/']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)
        self.assertEqual(self.client.get('/reportes/excel/?edad_min=50&edad_max=20').status_code, 400)

    def test_login_y_filtros_invalidos(self):
        self.assertContains(self.client.get('/cuentas/entrar/'), 'Iniciar sesión')
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get('/?edad_min=50&edad_max=20'), 'La edad mínima no puede superar la máxima.')

    def test_csrf_en_carga(self):
        from django.test import Client
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post('/importaciones/', {}).status_code, 403)

# Create your tests here.
