"""Catálogo de términos conocidos; no asigna categorías clínicas por defecto."""
import re

from .models import Enfermedad, clave_enfermedad

SIN_ENFERMEDAD = {
    'sin antecedentes', 'sin antecedentes morbidos relevantes', 'sin informacion',
    'no aplica', 'ninguna', 'ninguno',
}


def registrar_enfermedad(nombre):
    nombre = ' '.join(nombre.split())
    clave = clave_enfermedad(nombre)
    if not clave or clave in SIN_ENFERMEDAD or len(nombre) > 150:
        return None
    enfermedad, _ = Enfermedad.objects.get_or_create(clave=clave, defaults={'nombre': nombre})
    return enfermedad


def sincronizar_enfermedades(consulta):
    # Las comas pueden ser parte de un diagnóstico; no se usan como separador.
    nombres = re.split(r'[;\n]+', consulta.enfermedades_declaradas)
    nombres.extend(consulta.enfermedades)
    enfermedades = [e for nombre in nombres if (e := registrar_enfermedad(nombre)) is not None]
    consulta.enfermedades_registradas.set(enfermedades)
