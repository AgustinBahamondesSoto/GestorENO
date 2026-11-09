from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pacientes.models import Consulta
from indicadores.services import calcular_indicadores, filtrar_pacientes


def texto_excel(valor):
    """Evita que el texto de entrada se interprete como fórmula en Excel."""
    if isinstance(valor, str) and valor.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + valor
    return valor


def finalizar_libro(libro):
    for hoja in libro:
        hoja.freeze_panes = 'A2'
        hoja.auto_filter.ref = hoja.dimensions
        for celda in hoja[1]:
            celda.font = Font(bold=True, color='FFFFFF')
            celda.fill = PatternFill('solid', fgColor='16636A')
        for columna in hoja.columns:
            hoja.column_dimensions[columna[0].column_letter].width = min(60, max(14, max(len(str(c.value or '')) for c in columna) + 2))
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def generar_reporte(filtros=None):
    datos = calcular_indicadores(filtros)
    libro = Workbook()
    resumen = libro.active
    resumen.title = 'Resumen'
    resumen.append(['Indicador', 'Valor'])
    resumen.append(['Pacientes únicos por RUT', datos['total']])
    resumen.append(['Base de cálculo', 'Historial completo de pacientes filtrados; una persona puede aparecer en varias categorías.'])
    for clave, titulo in [('edades', 'Edad'), ('sexos', 'Sexo'), ('previsiones', 'Previsión'), ('categorias', 'GES y ENO'), ('enfermedades', 'Prevalencia')]:
        hoja = libro.create_sheet(titulo)
        hoja.append(['Grupo', 'Pacientes únicos', 'Porcentaje de la población filtrada'])
        for fila in datos[clave]:
            hoja.append([texto_excel(fila['nombre']), fila['cantidad'], fila['porcentaje']])
    pacientes = filtrar_pacientes(filtros)
    for titulo, condiciones in [('ENO pendientes', {'clasificacion': 'ENO', 'eno_notificado': False}), ('GES vigentes', {'clasificacion': 'GES_AUGE', 'ges_vigente': True})]:
        hoja = libro.create_sheet(titulo)
        hoja.append(['RUT', 'Nombre', 'Edad actual', 'Sexo', 'Previsión', 'Consultas del reporte', 'Enfermedades detectadas'])
        agrupadas = {}
        for c in Consulta.objects.filter(paciente__in=pacientes, **condiciones).select_related('paciente'):
            fila = agrupadas.setdefault(c.paciente_id, {'paciente': c.paciente, 'cantidad': 0, 'enfermedades': set()})
            fila['cantidad'] += 1
            fila['enfermedades'].update(c.enfermedades)
        for fila in agrupadas.values():
            p = fila['paciente']
            hoja.append([texto_excel(v) for v in [p.rut, p.nombre_completo, p.edad, p.sexo, p.prevision, fila['cantidad'], ', '.join(sorted(fila['enfermedades']))]])
    return finalizar_libro(libro)


def generar_plantilla():
    from importaciones.services import PLANTILLA_HOSPITAL
    libro = Workbook()
    libro.active.title = 'Pacientes'
    libro.active.append(PLANTILLA_HOSPITAL)
    return finalizar_libro(libro)
