from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from pacientes.models import Paciente, Consulta, CambioPaciente
from pacientes.services import registrar_consulta
from clasificacion.models import Enfermedad
from .eliminacion import eliminar_ultima_importacion
from .models import Importacion
from .services import importar_excel
from .tests import FILA, planilla


class EliminacionImportacionTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username='eliminacion')
        self.client.force_login(self.usuario)

    def cargar(self, filas, nombre='prueba.xlsx'):
        return importar_excel(planilla(filas), nombre, self.usuario)

    def test_borra_lote_consultas_pacientes_exclusivos_y_permite_reimportar(self):
        lote = self.cargar([FILA])
        resumen = eliminar_ultima_importacion(lote.pk)
        self.assertEqual(resumen['pacientes_eliminados'], 1)
        self.assertFalse(Importacion.objects.exists())
        self.assertFalse(Consulta.objects.exists())
        self.assertFalse(Paciente.objects.exists())
        self.assertEqual(self.cargar([FILA]).validas, 1)

    def test_comparte_paciente_restaura_maestro_y_conserva_lote_anterior(self):
        primero = self.cargar([FILA], 'anterior.xlsx')
        nueva = [*FILA]
        nueva[2], nueva[5], nueva[8] = 31, 'Isapre', '2026-11-10'
        adicional = [*FILA]
        adicional[1] = '1000005-K'
        ultimo = self.cargar([nueva, adicional], 'nuevo.xlsx')
        resumen = eliminar_ultima_importacion(ultimo.pk)
        paciente = Paciente.objects.get()
        self.assertEqual(paciente.edad, 30)
        self.assertEqual(paciente.prevision, FILA[5])
        self.assertEqual(Consulta.objects.get().importacion, primero)
        self.assertEqual(resumen['pacientes_eliminados'], 1)
        self.assertEqual(resumen['pacientes_conservados'], 1)

    def test_lote_historico_sin_snapshots_restaura_consulta_restante(self):
        self.cargar([FILA])
        nueva = [*FILA]
        nueva[2], nueva[8] = 45, '2026-11-10'
        ultimo = self.cargar([nueva])
        ultimo.estados_pacientes.all().delete()
        eliminar_ultima_importacion(ultimo.pk)
        self.assertEqual(Paciente.objects.get().edad, 30)

    def test_conserva_correccion_y_atencion_manuales_posteriores(self):
        self.cargar([FILA])
        nueva = [*FILA]
        nueva[2], nueva[8] = 31, '2026-11-10'
        ultimo = self.cargar([nueva])
        paciente = Paciente.objects.get()
        paciente.nombre = 'Nombre corregido manualmente'
        paciente.save()
        CambioPaciente.objects.create(paciente=paciente, usuario=self.usuario, accion='Modificación')
        manual = registrar_consulta(paciente, {
            'fecha': '2026-11-11', 'enfermedades': [], 'antecedentes': 'Control manual',
        }, self.usuario)
        eliminar_ultima_importacion(ultimo.pk)
        paciente.refresh_from_db()
        self.assertEqual(paciente.nombre, 'Nombre corregido manualmente')
        self.assertTrue(Consulta.objects.filter(pk=manual.pk).exists())

    def test_paciente_registrado_manualmente_antes_de_carga_se_conserva(self):
        paciente = Paciente.objects.create(rut='12345678-5', nombre='Nombre manual', edad=24, sexo='F', prevision='Isapre')
        CambioPaciente.objects.create(paciente=paciente, usuario=self.usuario, accion='Registro')
        lote = self.cargar([FILA])
        eliminar_ultima_importacion(lote.pk)
        paciente.refresh_from_db()
        self.assertEqual(paciente.nombre, 'Nombre manual')
        self.assertEqual(paciente.edad, 24)
        self.assertFalse(Consulta.objects.exists())

    def test_ficha_preexistente_sin_atenciones_ni_auditoria_no_se_borra(self):
        paciente = Paciente.objects.create(rut='12345678-5', nombre='Ficha preexistente', edad=24, sexo='F', prevision='Isapre')
        lote = self.cargar([FILA])
        eliminar_ultima_importacion(lote.pk)
        paciente.refresh_from_db()
        self.assertEqual(paciente.nombre, 'Ficha preexistente')
        self.assertEqual(paciente.prevision, 'Isapre')

    def test_carga_duplicada_no_borra_datos_de_la_primera(self):
        primero = self.cargar([FILA])
        segundo = self.cargar([FILA])
        self.assertEqual(segundo.omitidas, 1)
        resumen = eliminar_ultima_importacion(segundo.pk)
        self.assertEqual(resumen['consultas'], 0)
        self.assertEqual(Consulta.objects.get().importacion, primero)
        eliminar_ultima_importacion(primero.pk)
        self.assertFalse(Paciente.objects.exists())

    def test_no_se_borra_lote_antiguo_o_confirmacion_desactualizada(self):
        primero = self.cargar([FILA])
        self.assertEqual(self.client.get(f'/importaciones/{primero.pk}/eliminar/').status_code, 200)
        self.cargar([FILA])
        with self.assertRaises(ValidationError):
            eliminar_ultima_importacion(primero.pk)
        self.assertEqual(self.client.post(f'/importaciones/{primero.pk}/eliminar/', {'confirmar': 'si'}).status_code, 409)
        self.assertEqual(Importacion.objects.count(), 2)

    def test_get_y_post_sin_confirmacion_no_borran(self):
        lote = self.cargar([FILA])
        ruta = f'/importaciones/{lote.pk}/eliminar/'
        self.assertContains(self.client.get(ruta), 'Datos que se eliminarán')
        self.assertContains(self.client.post(ruta), 'Marca la confirmación')
        self.assertEqual(Consulta.objects.count(), 1)
        self.assertRedirects(self.client.post(ruta, {'confirmar': 'si'}), '/importaciones/')
        self.assertFalse(Consulta.objects.exists())

    def test_csrf_y_login(self):
        lote = self.cargar([FILA])
        ruta = f'/importaciones/{lote.pk}/eliminar/'
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post(ruta, {'confirmar': 'si'}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(ruta, {'confirmar': 'si'}).status_code, 302)
        self.assertTrue(Importacion.objects.exists())

    def test_fallo_de_restauracion_revierte_todo_el_borrado(self):
        self.cargar([FILA])
        nueva = [*FILA]
        nueva[2], nueva[8] = 31, '2026-11-10'
        ultimo = self.cargar([nueva])
        with patch.object(Paciente, 'save', side_effect=RuntimeError('Error simulado')):
            with self.assertRaises(RuntimeError):
                eliminar_ultima_importacion(ultimo.pk)
        self.assertEqual(Importacion.objects.count(), 2)
        self.assertEqual(Consulta.objects.count(), 2)
        self.assertEqual(Paciente.objects.get().edad, 31)

    def test_catalogo_de_enfermedades_no_se_elimina(self):
        fila = [*FILA]
        fila[6] = 'Antecedente ficticio'
        lote = self.cargar([fila])
        enfermedad = Enfermedad.objects.create(nombre='Enfermedad de prueba')
        eliminar_ultima_importacion(lote.pk)
        self.assertTrue(Enfermedad.objects.filter(pk=enfermedad.pk).exists())
