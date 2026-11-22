from urllib.parse import urlsplit
from base64 import b32decode
from unittest.mock import patch

from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.oath import TOTP
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice


class MFATests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='usuario_mfa_prueba', password='ClaveFicticiaSoloParaTests_2026',
        )
        self.clave = 'ClaveFicticiaSoloParaTests_2026'

    def dispositivo(self):
        return TOTPDevice.objects.create(
            user=self.usuario, name='default', confirmed=True,
        )

    def sesion_verificada(self, dispositivo):
        self.client.force_login(self.usuario)
        sesion = self.client.session
        sesion[DEVICE_ID_SESSION_KEY] = dispositivo.persistent_id
        sesion.save()

    def enviar_contrasena(self):
        url = reverse('two_factor:login')
        self.client.get(url)
        return self.client.post(url, {
            'login_view-current_step': 'auth',
            'auth-username': self.usuario.username,
            'auth-password': self.clave,
        })

    def test_login_nuevo_se_muestra(self):
        respuesta = self.client.get(reverse('two_factor:login'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'auth-username')

    def test_login_antiguo_solo_redirige(self):
        respuesta = self.client.post(reverse('login'), {
            'username': self.usuario.username, 'password': self.clave,
        })
        self.assertRedirects(respuesta, reverse('two_factor:login'))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_anonimo_no_accede_a_pacientes_ni_exportacion(self):
        for ruta in ('/pacientes/', '/reportes/excel/'):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertEqual(respuesta.status_code, 302)
                self.assertEqual(urlsplit(respuesta.url).path, reverse('two_factor:login'))
                self.assertNotIn('Content-Disposition', respuesta.headers)

    def test_usuario_sin_dispositivo_debe_configurarlo(self):
        self.client.force_login(self.usuario)
        for ruta in ('/', '/pacientes/', '/reportes/excel/', '/admin/'):
            with self.subTest(ruta=ruta):
                self.assertRedirects(self.client.get(ruta), reverse('two_factor:setup'))

    def test_usuario_con_dispositivo_sin_otp_no_accede(self):
        self.dispositivo()
        self.client.force_login(self.usuario)
        for ruta in ('/', '/pacientes/', '/reportes/excel/', '/admin/'):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertEqual(respuesta.status_code, 302)
                self.assertEqual(urlsplit(respuesta.url).path, reverse('two_factor:login'))
                self.assertNotIn('Content-Disposition', respuesta.headers)

    def test_no_se_reconfigura_dispositivo_sin_otp(self):
        self.dispositivo()
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('two_factor:setup'))
        self.assertEqual(urlsplit(respuesta.url).path, reverse('two_factor:login'))

    def test_sesion_verificada_accede_a_pacientes_y_reporte(self):
        self.sesion_verificada(self.dispositivo())
        self.assertEqual(self.client.get('/pacientes/').status_code, 200)
        reporte = self.client.get('/reportes/excel/')
        self.assertEqual(reporte.status_code, 200)
        self.assertIn('attachment', reporte.headers['Content-Disposition'])

    def test_administrador_necesita_otp_y_luego_accede(self):
        self.usuario.is_staff = True
        self.usuario.is_superuser = True
        self.usuario.save()
        dispositivo = self.dispositivo()
        self.client.force_login(self.usuario)
        respuesta = self.client.get('/admin/')
        self.assertEqual(urlsplit(respuesta.url).path, reverse('two_factor:login'))
        self.sesion_verificada(dispositivo)
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_contrasena_sola_no_crea_sesion_para_usuario_con_mfa(self):
        self.dispositivo()
        respuesta = self.enviar_contrasena()
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'token-otp_token')
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_codigo_invalido_no_autentica(self):
        self.dispositivo()
        self.enviar_contrasena()
        respuesta = self.client.post(reverse('two_factor:login'), {
            'login_view-current_step': 'token', 'token-otp_token': 'invalido',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_codigo_numerico_incorrecto_no_autentica(self):
        dispositivo = self.dispositivo()
        reloj = 1800000000
        generador = TOTP(dispositivo.bin_key, dispositivo.step, dispositivo.t0, dispositivo.digits)
        validos = set()
        for desfase in (-30, 0, 30):
            generador.time = reloj + desfase
            validos.add(generador.token())
        incorrecto = next(valor for valor in range(1000000) if valor not in validos)
        with patch('django_otp.plugins.otp_totp.models.time.time', return_value=reloj):
            self.enviar_contrasena()
            respuesta = self.client.post(reverse('two_factor:login'), {
                'login_view-current_step': 'token',
                'token-otp_token': str(incorrecto).zfill(6),
            })
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)
        dispositivo.refresh_from_db()
        self.assertGreater(dispositivo.throttling_failure_count, 0)

    def test_codigo_correcto_autentica_y_no_se_reutiliza(self):
        dispositivo = self.dispositivo()
        reloj = 1800000000
        generador = TOTP(dispositivo.bin_key, dispositivo.step, dispositivo.t0, dispositivo.digits)
        generador.time = reloj
        codigo = str(generador.token()).zfill(dispositivo.digits)
        with patch('django_otp.plugins.otp_totp.models.time.time', return_value=reloj):
            self.enviar_contrasena()
            respuesta = self.client.post(reverse('two_factor:login'), {
                'login_view-current_step': 'token', 'token-otp_token': codigo,
            })
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.client.session[DEVICE_ID_SESSION_KEY], dispositivo.persistent_id)
        self.assertEqual(self.client.get('/pacientes/').status_code, 200)
        dispositivo.refresh_from_db()
        with patch('django_otp.plugins.otp_totp.models.time.time', return_value=reloj):
            self.assertFalse(dispositivo.verify_token(codigo))

    def test_codigo_recuperacion_funciona_una_sola_vez(self):
        self.dispositivo()
        respaldo = StaticDevice.objects.create(user=self.usuario, name='backup')
        codigo = StaticToken.random_token()
        StaticToken.objects.create(device=respaldo, token=codigo)
        self.enviar_contrasena()
        self.client.post(reverse('two_factor:login'), {'wizard_goto_step': 'backup'})
        respuesta = self.client.post(reverse('two_factor:login'), {
            'login_view-current_step': 'backup', 'backup-otp_token': codigo,
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.client.session[DEVICE_ID_SESSION_KEY], respaldo.persistent_id)
        self.assertFalse(StaticToken.objects.filter(device=respaldo, token=codigo).exists())

    def test_login_y_configuracion_requieren_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(reverse('two_factor:login'), {}).status_code, 403)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post(reverse('two_factor:setup'), {}).status_code, 403)

    def test_salida_elimina_la_verificacion(self):
        self.sesion_verificada(self.dispositivo())
        self.client.post(reverse('logout'))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertNotIn(DEVICE_ID_SESSION_KEY, self.client.session)

    def test_configuracion_permite_mostrar_qr_sin_exponerlo_en_tests(self):
        self.client.force_login(self.usuario)
        url = reverse('two_factor:setup')
        self.assertEqual(self.client.get(url).status_code, 200)
        respuesta = self.client.post(url, {'setup_view-current_step': 'welcome'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'generator-token')
        self.assertEqual(self.client.get(reverse('two_factor:qr')).status_code, 200)

    def test_confirmacion_del_primer_autenticador_habilita_acceso(self):
        self.client.force_login(self.usuario)
        url = reverse('two_factor:setup')
        self.client.get(url)
        self.client.post(url, {'setup_view-current_step': 'welcome'})
        clave = b32decode(self.client.session['django_two_factor-qr_secret_key'])
        reloj = 1800000000
        generador = TOTP(clave)
        generador.time = reloj
        codigo = str(generador.token()).zfill(6)
        with (
            patch('two_factor.forms.time', return_value=reloj),
            patch('django_otp.oath.time', return_value=reloj),
        ):
            respuesta = self.client.post(url, {
                'setup_view-current_step': 'generator',
                'generator-token': codigo,
            })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(TOTPDevice.objects.filter(user=self.usuario, confirmed=True).exists())
        self.assertIn(DEVICE_ID_SESSION_KEY, self.client.session)
        self.assertEqual(self.client.get('/pacientes/').status_code, 200)
