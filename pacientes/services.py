from uuid import uuid4
from django.db import transaction
from clasificacion.catalogo import registrar_enfermedad
from clasificacion.services import actualizar_clasificacion
from .models import CambioPaciente, Consulta

CAMPOS_PACIENTE = ('rut', 'nombre', 'apellido', 'edad', 'sexo', 'prevision', 'domicilio_comuna')


def datos_paciente(paciente):
    return {campo: getattr(paciente, campo) for campo in CAMPOS_PACIENTE}


@transaction.atomic
def guardar_paciente(form, usuario, antes=None):
    paciente = form.save()
    despues = datos_paciente(paciente)
    if antes != despues:
        CambioPaciente.objects.create(
            paciente=paciente, usuario=usuario,
            accion='Modificación' if antes else 'Registro', antes=antes or {}, despues=despues,
        )
    return paciente


@transaction.atomic
def registrar_consulta(paciente, datos, usuario, consulta=None):
    enfermedades = list(datos['enfermedades'])
    if datos.get('enfermedad_nueva'):
        enfermedad = registrar_enfermedad(datos['enfermedad_nueva'])
        if enfermedad:
            enfermedades.append(enfermedad)
    nueva = consulta is None
    campos = ('fecha', 'peso', 'enfermedades_declaradas', 'antecedentes', 'signos_vitales', 'destino')
    antes = {k: str(getattr(consulta, k) or '') for k in campos} if consulta else {}
    if nueva:
        consulta = Consulta(
            paciente=paciente, huella='manual:' + uuid4().hex,
            nombre=paciente.nombre, apellido=paciente.apellido, edad=paciente.edad,
            sexo=paciente.sexo, prevision=paciente.prevision, domicilio_comuna=paciente.domicilio_comuna,
        )
    consulta.usuario = usuario
    consulta.fecha = datos['fecha']
    consulta.peso = datos.get('peso')
    consulta.enfermedades_declaradas = '; '.join(dict.fromkeys(e.nombre for e in enfermedades))
    for campo in ('antecedentes', 'signos_vitales', 'destino'):
        setattr(consulta, campo, datos.get(campo, ''))
    consulta.save()
    actualizar_clasificacion(consulta)
    CambioPaciente.objects.create(
        paciente=paciente, usuario=usuario,
        accion='Atención manual' if nueva else 'Corrección de atención', antes=antes,
        despues={**{k: str(getattr(consulta, k) or '') for k in campos}, 'consulta': consulta.pk, 'clasificacion': consulta.clasificacion},
    )
    return consulta
