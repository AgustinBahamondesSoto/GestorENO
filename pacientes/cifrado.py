from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _obtener_cifrador():
    clave = getattr(settings, 'CLAVE_CIFRADO', None)

    if clave is None:
        ruta = settings.BASE_DIR / '.env.clave_cifrado'

        try:
            clave = ruta.read_bytes().strip()
        except OSError as exc:
            raise ImproperlyConfigured(
                'No se pudo leer la clave de cifrado.'
            ) from exc

    try:
        return Fernet(clave)
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            'La clave de cifrado no tiene un formato válido.'
        ) from exc


def cifrar_texto(texto):
    return _obtener_cifrador().encrypt(
        texto.encode('utf-8')
    ).decode('ascii')


def descifrar_texto(texto_cifrado):
    return _obtener_cifrador().decrypt(
        texto_cifrado.encode('ascii')
    ).decode('utf-8')