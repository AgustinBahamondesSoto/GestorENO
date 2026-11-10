from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import Enfermedad, ReglaClasificacion, clave_enfermedad
from .catalogo import registrar_enfermedad
from .forms import EnfermedadForm, ReglaForm
from .services import reclasificar_historial


@login_required
def catalogo(request):
    busqueda = request.GET.get('q', '').strip()
    enfermedades = Enfermedad.objects.all()
    if busqueda:
        enfermedades = enfermedades.filter(nombre__icontains=busqueda)
    pagina = Paginator(enfermedades, 25).get_page(request.GET.get('page'))
    reglas = list(ReglaClasificacion.objects.all())
    for enfermedad in pagina:
        enfermedad.reglas = [r for r in reglas if clave_enfermedad(r.enfermedad) == enfermedad.clave]
    return render(request, 'clasificacion/catalogo.html', {
        'pagina': pagina, 'busqueda': busqueda,
        'reglas': reglas,
    })


@login_required
def enfermedad_nueva(request):
    form = EnfermedadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        enfermedad = form.save()
        messages.success(request, 'Enfermedad agregada. Puedes crear su regla de clasificación.')
        return redirect(f"{reverse('clasificacion:regla_nueva')}?enfermedad={enfermedad.pk}")
    return render(request, 'edicion.html', {'form': form, 'titulo': 'Agregar enfermedad', 'volver': 'clasificacion:catalogo'})


@login_required
def regla_editar(request, pk=None):
    regla = get_object_or_404(ReglaClasificacion, pk=pk) if pk else None
    initial = {}
    if request.GET.get('enfermedad'):
        enfermedad = get_object_or_404(Enfermedad, pk=request.GET['enfermedad'])
        initial = {'enfermedad_catalogo': enfermedad.pk, 'nombre': enfermedad.nombre, 'patron': enfermedad.nombre, 'tipo': 'PALABRA'}
    form = ReglaForm(request.POST or None, instance=regla, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            guardada = form.save()
            registrar_enfermedad(guardada.enfermedad)
            cantidad = reclasificar_historial()
        messages.success(request, f'Regla guardada. Se actualizaron {cantidad} consultas automáticamente.')
        return redirect('clasificacion:catalogo')
    return render(request, 'edicion.html', {
        'form': form, 'titulo': 'Editar regla' if pk else 'Crear regla de clasificación',
        'volver': 'clasificacion:catalogo',
        'ayuda': 'Al guardar se reclasifica el historial completo con las reglas activas. Una prioridad menor se aplica primero.',
    })


@login_required
@require_POST
def reclasificar(request):
    cantidad = reclasificar_historial()
    messages.success(request, f'Historial actualizado: {cantidad} consultas reclasificadas.')
    return redirect('clasificacion:catalogo')

# Create your views here.
