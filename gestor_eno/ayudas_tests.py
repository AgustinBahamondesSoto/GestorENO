from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice


def iniciar_sesion_verificada(cliente, usuario):
    """Fixture de sesión para pruebas funcionales posteriores al acceso MFA.

    No verifica códigos ni modifica la política del sistema. Las pruebas del
    acceso con contraseña y OTP permanecen en gestor_eno.test_mfa.
    """
    cliente.force_login(usuario)
    dispositivo, _ = TOTPDevice.objects.get_or_create(
        user=usuario,
        name='default',
        confirmed=True,
    )
    sesion = cliente.session
    sesion[DEVICE_ID_SESSION_KEY] = dispositivo.persistent_id
    sesion.save()
