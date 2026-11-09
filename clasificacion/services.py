"""Strategy para reglas configuradas por el administrador del diccionario."""
import re
import unicodedata
from abc import ABC, abstractmethod

from .models import ReglaClasificacion


def simplificar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if unicodedata.category(c) != 'Mn')


class EstrategiaRegla(ABC):
    @abstractmethod
    def aplicar(self, patron, texto):
        raise NotImplementedError


class ReglaPalabraClave(EstrategiaRegla):
    def aplicar(self, patron, texto):
        return bool(re.search(r'(?<!\w)' + re.escape(simplificar(patron.strip())) + r'(?!\w)', simplificar(texto)))


class ReglaExpresionRegular(EstrategiaRegla):
    def aplicar(self, patron, texto):
        return bool(re.search(patron, texto, re.IGNORECASE))


class MotorReconocimiento:
    def __init__(self, reglas=None):
        self.reglas = list(reglas if reglas is not None else ReglaClasificacion.objects.filter(activa=True))
        self.estrategias = {'PALABRA': ReglaPalabraClave(), 'REGEX': ReglaExpresionRegular()}

    def clasificar(self, antecedentes, signos_vitales, enfermedades=''):
        texto = f'{enfermedades}\n{antecedentes}\n{signos_vitales}'
        coincidencias = [r for r in self.reglas if self.estrategias[r.tipo].aplicar(r.patron, texto)]
        return {
            'clasificacion': coincidencias[0].categoria if coincidencias else 'SIN_ANTECEDENTES',
            'enfermedades': sorted({r.enfermedad for r in coincidencias}),
            'reglas_aplicadas': [{'id': r.pk, 'nombre': r.nombre, 'categoria': r.categoria, 'enfermedad': r.enfermedad} for r in coincidencias],
        }
