from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from clasificacion.models import ReglaClasificacion
from .forms import FiltrosForm
from .services import calcular_indicadores


@login_required
def panel(request):
    form = FiltrosForm(request.GET)
    datos = calcular_indicadores(form.cleaned_data) if form.is_valid() else None
    return render(request, 'indicadores/panel.html', {'form': form, 'datos': datos, 'hay_reglas': ReglaClasificacion.objects.filter(activa=True).exists(), 'consulta': request.GET.urlencode()})

# Create your views here.
