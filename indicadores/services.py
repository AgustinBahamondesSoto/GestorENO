from collections import Counter, defaultdict

from pacientes.repositories import RepositorioDjango
from pacientes.models import Consulta
from django.db.models import Prefetch

ETIQUETAS = {'ENO': 'ENO', 'GES_AUGE': 'GES/AUGE', 'SIN_ANTECEDENTES': 'Sin coincidencias'}


def condiciones_clinicas(filtros=None, prefijo=''):
    filtros = filtros or {}
    condiciones = {}
    if filtros.get('categoria'):
        condiciones[prefijo + 'clasificacion'] = filtros['categoria']
    if filtros.get('enfermedad'):
        enfermedad = filtros['enfermedad']
        condiciones[prefijo + 'enfermedades_registradas__pk'] = getattr(enfermedad, 'pk', enfermedad)
    return condiciones


def consultas_filtradas(filtros=None):
    return Consulta.objects.filter(**condiciones_clinicas(filtros)).distinct()


def filtrar_pacientes(filtros=None, repositorio=None):
    filtros = filtros or {}
    pacientes = (repositorio or RepositorioDjango()).consultar()
    for clave, lookup in [('edad_min', 'edad__gte'), ('edad_max', 'edad__lte'), ('sexo', 'sexo__iexact'), ('prevision', 'prevision__iexact')]:
        if filtros.get(clave) is not None and filtros.get(clave) != '':
            pacientes = pacientes.filter(**{lookup: filtros[clave]})
    if condiciones := condiciones_clinicas(filtros, 'consultas__'):
        # Una misma consulta debe cumplir enfermedad y categoría.
        pacientes = pacientes.filter(**condiciones)
    return pacientes.distinct()


def pacientes_con_consultas(filtros=None, repositorio=None):
    consultas = consultas_filtradas(filtros).prefetch_related('enfermedades_registradas')
    return filtrar_pacientes(filtros, repositorio).prefetch_related(
        Prefetch('consultas', queryset=consultas, to_attr='consultas_del_resultado'),
    )


def resultados_pacientes(filtros=None):
    for paciente in pacientes_con_consultas(filtros):
        consultas = paciente.consultas_del_resultado
        yield {
            'paciente': paciente,
            'enfermedades': sorted({e.nombre for c in consultas for e in c.enfermedades_registradas.all()}),
            'clasificaciones': sorted({ETIQUETAS[c.clasificacion] for c in consultas}) or ['Sin atenciones'],
        }


def calcular_indicadores(filtros=None, repositorio=None):
    pacientes = list(pacientes_con_consultas(filtros, repositorio))
    total = len(pacientes)
    edades, sexos, previsiones = Counter(), Counter(), Counter()
    categorias, enfermedades = defaultdict(set), defaultdict(set)
    for p in pacientes:
        tramo = '0–14' if p.edad < 15 else '15–29' if p.edad < 30 else '30–44' if p.edad < 45 else '45–59' if p.edad < 60 else '60 o más'
        edades[tramo] += 1
        sexos[p.sexo] += 1
        previsiones[p.prevision] += 1
        for c in p.consultas_del_resultado:
            categorias[c.clasificacion].add(p.pk)
            for enfermedad in c.enfermedades_registradas.all():
                enfermedades[enfermedad.nombre].add(p.pk)

    def filas(conteos):
        return [{'nombre': k, 'cantidad': v, 'porcentaje': round(v * 100 / total, 2) if total else 0} for k, v in sorted(conteos.items())]

    return {'total': total, 'edades': filas(edades), 'sexos': filas(sexos), 'previsiones': filas(previsiones), 'categorias': filas({ETIQUETAS[k]: len(v) for k, v in categorias.items()}), 'enfermedades': filas({k: len(v) for k, v in enfermedades.items()})}
