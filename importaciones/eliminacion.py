"""Eliminación transaccional del último lote, sin afectar otros orígenes."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from pacientes.models import Paciente
from .models import Importacion
from .services import CAMPOS_MAESTRO


def ultima_importacion():
    return Importacion.objects.order_by('-creada', '-pk').first()


def pacientes_del_lote(lote):
    return Paciente.objects.filter(
        Q(consultas__importacion=lote) | Q(estados_importacion__importacion=lote),
    ).distinct()


def tiene_otro_origen(paciente, lote):
    return (
        paciente.consultas.exclude(importacion=lote).exists()
        or paciente.cambios.exists()
        or paciente.estados_importacion.exclude(importacion=lote).exists()
        or lote.estados_pacientes.filter(paciente=paciente).exclude(antes={}).exists()
    )


def resumen_eliminacion(lote):
    pacientes = list(pacientes_del_lote(lote))
    eliminados = sum(not tiene_otro_origen(p, lote) for p in pacientes)
    return {
        'consultas': lote.consultas.count(),
        'inconsistencias': lote.inconsistencias.count(),
        'pacientes_eliminados': eliminados,
        'pacientes_conservados': len(pacientes) - eliminados,
    }


@transaction.atomic
def eliminar_ultima_importacion(pk):
    ultima = Importacion.objects.select_for_update().order_by('-creada', '-pk').first()
    if ultima is None or ultima.pk != pk:
        raise ValidationError('Solo se puede eliminar la última importación. Actualiza la página y revisa el archivo seleccionado.')
    lote = ultima
    ids_pacientes = pacientes_del_lote(lote).order_by().values('pk')
    pacientes = list(Paciente.objects.select_for_update().filter(pk__in=ids_pacientes))
    resumen = resumen_eliminacion(lote)
    restauraciones = []
    borrar = []
    for paciente in pacientes:
        if not tiene_otro_origen(paciente, lote):
            borrar.append(paciente.pk)
            continue
        estado = lote.estados_pacientes.filter(paciente=paciente).first()
        restante = paciente.consultas.exclude(importacion=lote).order_by('-fecha', '-registrada', '-pk').first()
        eliminada = paciente.consultas.filter(importacion=lote).order_by('-fecha', '-registrada', '-pk').first()
        if estado:
            antes, despues = estado.antes, estado.despues
            if not antes and restante:
                antes = {k: getattr(restante, k) for k in CAMPOS_MAESTRO}
        else:
            # Compatibilidad con lotes importados antes de guardar snapshots.
            antes = {k: getattr(restante, k) for k in CAMPOS_MAESTRO} if restante else {}
            despues = {k: getattr(eliminada, k) for k in CAMPOS_MAESTRO} if eliminada else {}
        cambiados = []
        for campo in CAMPOS_MAESTRO:
            if campo in antes and getattr(paciente, campo) == despues.get(campo):
                if getattr(paciente, campo) != antes[campo]:
                    setattr(paciente, campo, antes[campo])
                    cambiados.append(campo)
        if cambiados:
            restauraciones.append((paciente, cambiados))
    # PROTECT se mantiene en los modelos; se borran únicamente estas consultas.
    lote.consultas.all().delete()
    lote.delete()
    Paciente.objects.filter(pk__in=borrar).delete()
    for paciente, campos in restauraciones:
        paciente.save(update_fields=[*campos, 'actualizado'])
    return resumen
