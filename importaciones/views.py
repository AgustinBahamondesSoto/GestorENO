from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ImportarForm
from .models import Importacion
from .services import importar_excel, ErrorPlantilla


@login_required
def importar(request):
    form = ImportarForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        archivo = form.cleaned_data['archivo']
        try:
            lote = importar_excel(archivo, archivo.name, request.user)
        except ErrorPlantilla as exc:
            form.add_error('archivo', str(exc))
        else:
            return redirect('importaciones:detalle', pk=lote.pk)
    return render(request, 'importaciones/importar.html', {'form': form, 'lotes': Importacion.objects.all()[:20]})


@login_required
def detalle(request, pk):
    lote = get_object_or_404(Importacion, pk=pk)
    return render(request, 'importaciones/detalle.html', {'lote': lote})

# Create your views here.
