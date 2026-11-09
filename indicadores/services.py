from collections import Counter, defaultdict

from pacientes.repositories import RepositorioDjango


def filtrar_pacientes(filtros=None, repositorio=None):
    filtros = filtros or {}
    pacientes = (repositorio or RepositorioDjango()).consultar()
    for clave, lookup in [('edad_min', 'edad__gte'), ('edad_max', 'edad__lte'), ('sexo', 'sexo__iexact'), ('prevision', 'prevision__iexact')]:
        if filtros.get(clave) is not None and filtros.get(clave) != '':
            pacientes = pacientes.filter(**{lookup: filtros[clave]})
    if filtros.get('categoria'):
        pacientes = pacientes.filter(consultas__clasificacion=filtros['categoria'])
    return pacientes.distinct()


def calcular_indicadores(filtros=None, repositorio=None):
    pacientes = list(filtrar_pacientes(filtros, repositorio).prefetch_related('consultas'))
    total = len(pacientes)
    edades, sexos, previsiones = Counter(), Counter(), Counter()
    categorias, enfermedades = defaultdict(set), defaultdict(set)
    for p in pacientes:
        tramo = '0–14' if p.edad < 15 else '15–29' if p.edad < 30 else '30–44' if p.edad < 45 else '45–59' if p.edad < 60 else '60 o más'
        edades[tramo] += 1
        sexos[p.sexo] += 1
        previsiones[p.prevision] += 1
        for c in p.consultas.all():
            categorias[c.clasificacion].add(p.pk)
            for enfermedad in c.enfermedades:
                enfermedades[enfermedad].add(p.pk)

    def filas(conteos):
        return [{'nombre': k, 'cantidad': v, 'porcentaje': round(v * 100 / total, 2) if total else 0} for k, v in sorted(conteos.items())]

    etiquetas = {'ENO': 'ENO', 'GES_AUGE': 'GES/AUGE', 'SIN_ANTECEDENTES': 'Sin coincidencias'}
    return {'total': total, 'edades': filas(edades), 'sexos': filas(sexos), 'previsiones': filas(previsiones), 'categorias': filas({etiquetas[k]: len(v) for k, v in categorias.items()}), 'enfermedades': filas({k: len(v) for k, v in enfermedades.items()})}
