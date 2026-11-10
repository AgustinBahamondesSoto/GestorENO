from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from importaciones.services import importar_excel
from importaciones.tests import planilla, FILA
from pacientes.models import Consulta
from .catalogo import registrar_enfermedad
from .models import Enfermedad, ReglaClasificacion


class ReglasWebTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username='funcionaria')
        self.client.force_login(self.usuario)
        fila = [*FILA]
        fila[6] = 'Condición de prueba alfa'
        importar_excel(planilla([fila]), 'demo.xlsx')
        self.enfermedad = registrar_enfermedad('Condición de prueba alfa')
        self.datos = {
            'nombre': 'Regla alfa', 'enfermedad_catalogo': self.enfermedad.pk,
            'categoria': 'ENO', 'tipo': 'PALABRA', 'patron': 'condición de prueba alfa',
            'prioridad': 10, 'activa': 'on',
        }

    def test_regla_desde_web_reclasifica_sin_ser_staff(self):
        respuesta = self.client.post('/clasificacion/reglas/nueva/', self.datos)
        self.assertRedirects(respuesta, '/clasificacion/')
        consulta = Consulta.objects.get()
        self.assertEqual(consulta.clasificacion, 'ENO')
        self.assertFalse(consulta.eno_notificado)
        self.assertEqual(consulta.enfermedades, ['Condición de prueba alfa'])
        self.assertContains(self.client.get('/clasificacion/'), 'Regla alfa')

    def test_desactivar_ultima_regla_limpia_resultados_obsoletos(self):
        self.client.post('/clasificacion/reglas/nueva/', self.datos)
        regla = ReglaClasificacion.objects.get()
        datos = {**self.datos}
        datos.pop('activa')
        self.client.post(f'/clasificacion/reglas/{regla.pk}/editar/', datos)
        consulta = Consulta.objects.get()
        self.assertEqual(consulta.clasificacion, 'SIN_ANTECEDENTES')
        self.assertEqual(consulta.enfermedades, [])
        self.assertFalse(consulta.reglas_aplicadas)

    def test_regex_invalida_no_guarda_ni_reclasifica(self):
        respuesta = self.client.post('/clasificacion/reglas/nueva/', {**self.datos, 'tipo': 'REGEX', 'patron': '['})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Expresión regular inválida')
        self.assertFalse(ReglaClasificacion.objects.exists())
        self.assertEqual(Consulta.objects.get().clasificacion, 'SIN_ANTECEDENTES')

    def test_agregar_enfermedad_y_evitar_duplicados_con_tildes(self):
        respuesta = self.client.post('/clasificacion/enfermedades/nueva/', {'nombre': 'Nueva condición ficticia'})
        enfermedad = Enfermedad.objects.get(clave='nueva condicion ficticia')
        self.assertRedirects(respuesta, f'/clasificacion/reglas/nueva/?enfermedad={enfermedad.pk}')
        respuesta = self.client.post('/clasificacion/enfermedades/nueva/', {'nombre': '  NUEVA CONDICION FICTICIA '})
        self.assertContains(respuesta, 'ya está en el catálogo')
        self.assertEqual(Enfermedad.objects.filter(clave=enfermedad.clave).count(), 1)

    def test_actualizacion_solo_post_autenticado_y_csrf(self):
        self.assertEqual(self.client.get('/clasificacion/reclasificar/').status_code, 405)
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post('/clasificacion/reclasificar/').status_code, 403)
        self.client.logout()
        for ruta in ['/clasificacion/', '/clasificacion/reglas/nueva/', '/clasificacion/enfermedades/nueva/']:
            self.assertEqual(self.client.get(ruta).status_code, 302)
