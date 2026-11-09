from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Paciente


@login_required
def listado(request):
    busqueda = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.all()
    if busqueda:
        pacientes = pacientes.filter(Q(nombre__icontains=busqueda) | Q(apellido__icontains=busqueda) | Q(rut__icontains=busqueda.replace('.', '').replace(' ', '').upper()))
    pagina = Paginator(pacientes, 25).get_page(request.GET.get('page'))
    return render(request, 'pacientes/listado.html', {'pagina': pagina, 'busqueda': busqueda})


@login_required
def detalle(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    pagina = Paginator(paciente.consultas.all(), 25).get_page(request.GET.get('page'))
    return render(request, 'pacientes/detalle.html', {'paciente': paciente, 'pagina': pagina})

# Create your views here.
