import json

from cryptography.fernet import InvalidToken
from django.core.exceptions import FieldError
from django.db import models

from .cifrado import cifrar_texto, descifrar_texto


PREFIJO = 'eno:v1:'


def _cifrar(valor):
    return PREFIJO + cifrar_texto(valor)


def _descifrar(valor):
    if not isinstance(valor, str) or not valor.startswith(PREFIJO):
        raise InvalidToken(
            'El valor almacenado no tiene el formato cifrado esperado.'
        )

    return descifrar_texto(valor[len(PREFIJO):])


class SoloConsultaNulos:
    """Evita búsquedas que no funcionan sobre contenido cifrado."""

    def get_lookup(self, nombre):
        if nombre != 'isnull':
            raise FieldError(
                'Este campo cifrado solo admite el filtro isnull.'
            )

        return super().get_lookup(nombre)

    def get_transform(self, nombre):
        raise FieldError(
            'No se pueden aplicar transformaciones a un campo cifrado.'
        )


class TextoCifrado(SoloConsultaNulos, models.TextField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)

        if value is None:
            return None

        return _cifrar(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None

        return _descifrar(value)


class JSONCifrado(SoloConsultaNulos, models.JSONField):
    def get_prep_value(self, value):
        if value is None:
            return None

        texto = json.dumps(
            value,
            cls=self.encoder,
            ensure_ascii=False,
        )

        return _cifrar(texto)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None

        token = super().from_db_value(
            value,
            expression,
            connection,
        )

        return json.loads(
            _descifrar(token),
            cls=self.decoder,
        )