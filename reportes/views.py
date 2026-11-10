from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from indicadores.forms import FiltrosForm
from .services import generar_reporte, generar_plantilla


def descarga(contenido, nombre):
    response = HttpResponse(contenido, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    response['Cache-Control'] = 'no-store'
    return response


@login_required
def exportar(request):
    filtros = FiltrosForm(request.GET)
    if not filtros.is_valid():
        return HttpResponse('Filtros inválidos. Revise edad, sexo, previsión, categoría y enfermedad.', status=400)
    return descarga(generar_reporte(filtros.cleaned_data), 'reporte_gestor_eno.xlsx')


@login_required
def plantilla(request):
    return descarga(generar_plantilla(), 'plantilla_pacientes.xlsx')

# Create your views here.
