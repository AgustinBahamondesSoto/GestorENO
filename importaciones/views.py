from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ImportarForm
from .models import Importacion
from .services import importar_excel, ErrorPlantilla
from .eliminacion import ultima_importacion, resumen_eliminacion, eliminar_ultima_importacion
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods


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
    return render(request, 'importaciones/importar.html', {
        'form': form, 'lotes': Importacion.objects.all()[:20], 'ultima': ultima_importacion(),
    })


@login_required
def detalle(request, pk):
    lote = get_object_or_404(Importacion, pk=pk)
    return render(request, 'importaciones/detalle.html', {'lote': lote, 'ultima': ultima_importacion()})


@login_required
@require_http_methods(['GET', 'POST'])
def eliminar(request, pk):
    lote = get_object_or_404(Importacion, pk=pk)
    ultima = ultima_importacion()
    if ultima is None or ultima.pk != lote.pk:
        return render(request, 'importaciones/eliminar.html', {'lote': lote, 'desactualizada': True}, status=409)
    resumen = resumen_eliminacion(lote)
    error = None
    if request.method == 'POST':
        if request.POST.get('confirmar') != 'si':
            error = 'Marca la confirmación para eliminar esta importación y sus datos.'
        else:
            try:
                resultado = eliminar_ultima_importacion(lote.pk)
            except ValidationError as exc:
                return render(request, 'importaciones/eliminar.html', {
                    'lote': lote, 'desactualizada': True, 'error': '; '.join(exc.messages),
                }, status=409)
            messages.success(request, (
                f'Importación eliminada: {resultado["consultas"]} consultas y '
                f'{resultado["pacientes_eliminados"]} pacientes exclusivos borrados. '
                f'Se conservaron {resultado["pacientes_conservados"]} pacientes con otros registros.'
            ))
            return redirect('importaciones:importar')
    return render(request, 'importaciones/eliminar.html', {'lote': lote, 'resumen': resumen, 'error': error})

# Create your views here.
