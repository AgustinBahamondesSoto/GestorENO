from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from clasificacion.models import ReglaClasificacion
from .forms import FiltrosForm
from .services import calcular_indicadores, resultados_pacientes
from django.core.paginator import Paginator


@login_required
def panel(request):
    form = FiltrosForm(request.GET)
    valido = form.is_valid()
    datos = calcular_indicadores(form.cleaned_data) if valido else None
    resultados = list(resultados_pacientes(form.cleaned_data)) if valido else []
    pagina = Paginator(resultados, 25).get_page(request.GET.get('page'))
    consulta = request.GET.copy()
    consulta.pop('page', None)
    return render(request, 'indicadores/panel.html', {
        'form': form, 'datos': datos, 'pagina': pagina,
        'hay_reglas': ReglaClasificacion.objects.filter(activa=True).exists(),
        'consulta': consulta.urlencode(),
    })

# Create your views here.
