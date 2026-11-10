from django.contrib.auth import get_user_model
from django.test import TestCase
from importaciones.services import importar_excel
from importaciones.tests import planilla, FILA
from clasificacion.catalogo import registrar_enfermedad
from clasificacion.models import ReglaClasificacion, Enfermedad
from .models import Paciente, Consulta, CambioPaciente


class PacientesWebTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username='valeria_prueba')
        self.client.force_login(self.usuario)
        self.datos = {
            'rut': '12.345.678-5', 'nombre': 'Persona', 'apellido': 'Ficticia',
            'edad': 30, 'sexo': 'F', 'prevision': 'Fonasa A',
            'domicilio_comuna': 'Domicilio ficticio, Valdivia, Región de Los Ríos',
        }

    def test_registrar_y_corregir_paciente_con_auditoria(self):
        respuesta = self.client.post('/pacientes/nuevo/', self.datos)
        paciente = Paciente.objects.get()
        self.assertRedirects(respuesta, f'/pacientes/{paciente.pk}/')
        self.assertEqual(paciente.rut, '12345678-5')
        respuesta = self.client.post(f'/pacientes/{paciente.pk}/editar/', {**self.datos, 'edad': 31})
        paciente.refresh_from_db()
        self.assertEqual(paciente.edad, 31)
        cambio = CambioPaciente.objects.filter(accion='Modificación').get()
        self.assertEqual(cambio.antes['edad'], 30)
        self.assertEqual(cambio.despues['edad'], 31)
        self.assertEqual(cambio.usuario, self.usuario)

    def test_rut_duplicado_o_invalido_no_crea_paciente(self):
        self.client.post('/pacientes/nuevo/', self.datos)
        for rut in ['12345678-5', '12345678-9']:
            respuesta = self.client.post('/pacientes/nuevo/', {**self.datos, 'rut': rut})
            self.assertEqual(respuesta.status_code, 200)
            self.assertTrue(respuesta.context['form'].errors)
        self.assertEqual(Paciente.objects.count(), 1)

    def test_correccion_de_ficha_conserva_snapshot_importado(self):
        importar_excel(planilla([FILA]), 'original.xlsx')
        paciente = Paciente.objects.get()
        self.client.post(f'/pacientes/{paciente.pk}/editar/', {**self.datos, 'edad': 45})
        self.assertEqual(Consulta.objects.get().edad, 30)
        paciente.refresh_from_db()
        self.assertEqual(paciente.edad, 45)

    def test_agregar_enfermedad_existente_y_clasificacion_inmediata(self):
        self.client.post('/pacientes/nuevo/', self.datos)
        paciente = Paciente.objects.get()
        enfermedad = registrar_enfermedad('Condición ficticia')
        ReglaClasificacion.objects.create(nombre='Regla', enfermedad=enfermedad.nombre, categoria='GES_AUGE', tipo='PALABRA', patron=enfermedad.nombre)
        respuesta = self.client.post(f'/pacientes/{paciente.pk}/atenciones/nueva/', {
            'fecha': '2026-11-10', 'enfermedades': [enfermedad.pk], 'antecedentes': 'Control de prueba',
        })
        self.assertRedirects(respuesta, f'/pacientes/{paciente.pk}/')
        consulta = Consulta.objects.get()
        self.assertIsNone(consulta.importacion)
        self.assertIsNone(consulta.peso)
        self.assertEqual(consulta.clasificacion, 'GES_AUGE')
        self.assertTrue(consulta.ges_vigente)
        self.assertEqual(consulta.usuario, self.usuario)

    def test_enfermedad_nueva_y_correccion_de_atencion_con_traza(self):
        importar_excel(planilla([FILA]), 'original.xlsx')
        consulta = Consulta.objects.get()
        huella_original = consulta.huella
        ruta = f'/pacientes/{consulta.paciente_id}/atenciones/{consulta.pk}/editar/'
        respuesta = self.client.post(ruta, {
            'fecha': '2026-11-10', 'enfermedad_nueva': 'Nueva condición de prueba',
            'antecedentes': 'Antecedente corregido',
        })
        self.assertEqual(respuesta.status_code, 302)
        consulta.refresh_from_db()
        self.assertTrue(Enfermedad.objects.filter(nombre='Nueva condición de prueba').exists())
        self.assertEqual(consulta.huella, huella_original)
        self.assertEqual(consulta.clasificacion, 'SIN_ANTECEDENTES')
        self.assertIsNotNone(consulta.importacion)
        cambio = CambioPaciente.objects.get(accion='Corrección de atención')
        self.assertEqual(cambio.antes['antecedentes'], FILA[6])
        self.assertEqual(cambio.despues['antecedentes'], 'Antecedente corregido')
        lote = importar_excel(planilla([FILA]), 'reimportada.xlsx')
        self.assertEqual(lote.omitidas, 1)
        self.assertEqual(Consulta.objects.count(), 1)

    def test_no_se_edita_consulta_de_otro_paciente(self):
        importar_excel(planilla([FILA]), 'original.xlsx')
        otro = Paciente.objects.create(rut='1000005-K', nombre='Otra persona', edad=40, sexo='M', prevision='Isapre')
        self.assertEqual(self.client.get(f'/pacientes/{otro.pk}/atenciones/{Consulta.objects.get().pk}/editar/').status_code, 404)

    def test_formularios_requieren_login(self):
        self.client.logout()
        self.assertEqual(self.client.get('/pacientes/nuevo/').status_code, 302)
