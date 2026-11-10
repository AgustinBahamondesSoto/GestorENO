"""Strategy para reglas configuradas por el administrador del diccionario."""
import re
import unicodedata
from abc import ABC, abstractmethod

from .models import ReglaClasificacion
from django.db import transaction


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


def actualizar_clasificacion(consulta, motor=None):
    from .catalogo import sincronizar_enfermedades

    motor = motor or MotorReconocimiento()
    resultado = motor.clasificar(consulta.antecedentes, consulta.signos_vitales, consulta.enfermedades_declaradas)
    nueva = resultado['clasificacion']
    anterior = consulta.clasificacion
    if nueva != anterior:
        consulta.ges_vigente = nueva == 'GES_AUGE'
        consulta.eno_notificado = False
    for campo, valor in resultado.items():
        setattr(consulta, campo, valor)
    consulta.save(update_fields=[*resultado, 'ges_vigente', 'eno_notificado'])
    sincronizar_enfermedades(consulta)


@transaction.atomic
def reclasificar_historial():
    from pacientes.models import Consulta

    motor = MotorReconocimiento()
    cantidad = 0
    # También se procesa con cero reglas: evita dejar clasificaciones obsoletas.
    for consulta in Consulta.objects.all().iterator():
        actualizar_clasificacion(consulta, motor)
        cantidad += 1
    return cantidad
