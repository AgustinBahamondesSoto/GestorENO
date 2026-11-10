from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Paciente, Consulta
from clasificacion.models import clave_enfermedad
import re
from django.shortcuts import redirect
from django.contrib import messages
from .forms import PacienteForm, ConsultaManualForm
from .services import guardar_paciente, datos_paciente, registrar_consulta


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


@login_required
def editar(request, pk=None):
    paciente = get_object_or_404(Paciente, pk=pk) if pk else None
    antes = datos_paciente(paciente) if paciente else None
    form = PacienteForm(request.POST or None, instance=paciente)
    if request.method == 'POST' and form.is_valid():
        paciente = guardar_paciente(form, request.user, antes)
        messages.success(request, 'Paciente guardado. Sus consultas anteriores se conservaron.')
        return redirect('pacientes:detalle', pk=paciente.pk)
    return render(request, 'edicion.html', {
        'form': form, 'titulo': 'Editar paciente' if pk else 'Registrar paciente',
        'volver': 'pacientes:listado',
        'ayuda': 'El RUT identifica al paciente. Las correcciones actualizan su ficha y quedan registradas sin modificar las consultas anteriores.',
    })


@login_required
def agregar_consulta(request, pk, consulta_pk=None):
    paciente = get_object_or_404(Paciente, pk=pk)
    consulta = get_object_or_404(Consulta, pk=consulta_pk, paciente=paciente) if consulta_pk else None
    initial = {}
    if consulta:
        claves = {clave_enfermedad(n) for n in re.split(r'[;\n]+', consulta.enfermedades_declaradas)}
        initial = {
            'fecha': consulta.fecha,
            'peso': consulta.peso, 'antecedentes': consulta.antecedentes,
            'signos_vitales': consulta.signos_vitales, 'destino': consulta.destino,
            'enfermedades': list(consulta.enfermedades_registradas.filter(clave__in=claves).values_list('pk', flat=True)),
        }
    form = ConsultaManualForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        consulta = registrar_consulta(paciente, form.cleaned_data, request.user, consulta)
        messages.success(request, f'Atención registrada. Clasificación: {consulta.get_clasificacion_display()}.')
        return redirect('pacientes:detalle', pk=paciente.pk)
    return render(request, 'pacientes/consulta_form.html', {'form': form, 'paciente': paciente, 'editando': consulta is not None})

# Create your views here.
