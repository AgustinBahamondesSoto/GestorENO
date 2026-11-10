from django import forms
from django.utils import timezone
from clasificacion.forms import estilo_formulario
from clasificacion.models import Enfermedad
from clasificacion.models import clave_enfermedad
from clasificacion.catalogo import SIN_ENFERMEDAD
from .models import Paciente
from .validators import normalizar_rut

SEXO = [('F', 'Femenino'), ('M', 'Masculino'), ('Otro', 'Otro'), ('Sin información', 'Sin información')]
PREVISION = ['Fonasa A', 'Fonasa B', 'Fonasa C', 'Fonasa D', 'Fonasa', 'Isapre', 'Particular', 'Sin información']


class PacienteForm(forms.ModelForm):
    rut = forms.CharField(label='RUT', max_length=20, help_text='Con o sin puntos; se valida el dígito verificador.')
    sexo = forms.ChoiceField(choices=[('', 'Selecciona sexo'), *SEXO])
    prevision = forms.ChoiceField(label='Previsión')

    class Meta:
        model = Paciente
        fields = ['rut', 'nombre', 'apellido', 'edad', 'sexo', 'prevision', 'domicilio_comuna']
        labels = {'rut': 'RUT', 'nombre': 'Nombres', 'apellido': 'Apellidos'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        previsiones = sorted(set(PREVISION) | set(Paciente.objects.values_list('prevision', flat=True)))
        self.fields['prevision'].choices = [('', 'Selecciona previsión'), *[(p, p) for p in previsiones if p]]
        sexos = dict(SEXO)
        if self.instance.pk and self.instance.sexo not in sexos:
            self.fields['sexo'].choices = [*SEXO, (self.instance.sexo, self.instance.sexo)]
        estilo_formulario(self)

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data['rut'])


class ConsultaManualForm(forms.Form):
    fecha = forms.DateField(label='Fecha de atención', initial=timezone.localdate, widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    enfermedades = forms.ModelMultipleChoiceField(
        queryset=Enfermedad.objects.all(), required=False,
        label='Enfermedades del catálogo',
        help_text='Puedes seleccionar varias enfermedades. Se conservan las atenciones anteriores.',
    )
    enfermedad_nueva = forms.CharField(
        label='Otra enfermedad', max_length=150, required=False,
        help_text='Si no está en el catálogo, escribe aquí su nombre para incorporarla.',
    )
    peso = forms.DecimalField(label='Peso (kg)', min_value=0.01, max_digits=6, decimal_places=2, required=False)
    antecedentes = forms.CharField(label='Antecedentes médicos', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    signos_vitales = forms.CharField(label='Signos vitales', widget=forms.Textarea(attrs={'rows': 2}), required=False)
    destino = forms.CharField(label='Destino del paciente', max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilo_formulario(self)

    def clean(self):
        datos = super().clean()
        if not datos.get('enfermedades') and not datos.get('enfermedad_nueva') and not datos.get('antecedentes'):
            raise forms.ValidationError('Selecciona una enfermedad, agrega una nueva o registra antecedentes médicos.')
        return datos

    def clean_enfermedad_nueva(self):
        nombre = ' '.join(self.cleaned_data['enfermedad_nueva'].split())
        if nombre and clave_enfermedad(nombre) in SIN_ENFERMEDAD:
            raise forms.ValidationError('Escribe un nombre de enfermedad. Para indicar ausencia de antecedentes utiliza el campo Antecedentes médicos.')
        return nombre
