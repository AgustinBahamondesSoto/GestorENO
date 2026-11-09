import re

from django.core.exceptions import ValidationError


def normalizar_rut(valor):
    """Devuelve cuerpo-DV validado mediante módulo 11."""
    rut = re.sub(r'[.\s]', '', str(valor or '')).upper()
    if not re.fullmatch(r'\d{1,8}-?[0-9K]', rut):
        raise ValidationError('RUT vacío o con formato inválido.')
    cuerpo, dv = rut.replace('-', '')[:-1], rut[-1]
    cuerpo = str(int(cuerpo))
    if int(cuerpo) == 0:
        raise ValidationError('El cuerpo del RUT debe ser mayor que cero.')
    suma = sum(int(n) * (2 + i % 6) for i, n in enumerate(reversed(cuerpo)))
    resultado = 11 - suma % 11
    esperado = '0' if resultado == 11 else 'K' if resultado == 10 else str(resultado)
    if dv != esperado:
        raise ValidationError('Dígito verificador del RUT incorrecto.')
    return f'{cuerpo}-{dv}'
