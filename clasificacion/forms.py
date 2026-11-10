from django import forms
from .models import Enfermedad, ReglaClasificacion, clave_enfermedad


def estilo_formulario(form):
    for field in form.fields.values():
        widget = field.widget
        widget.attrs['class'] = (
            'form-check-input' if isinstance(widget, forms.CheckboxInput)
            else 'form-select' if isinstance(widget, forms.Select)
            else 'form-control'
        )


class EnfermedadForm(forms.ModelForm):
    class Meta:
        model = Enfermedad
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilo_formulario(self)

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if Enfermedad.objects.filter(clave=clave_enfermedad(nombre)).exists():
            raise forms.ValidationError('Esta enfermedad ya está en el catálogo.')
        return nombre


class ReglaForm(forms.ModelForm):
    enfermedad_catalogo = forms.ModelChoiceField(
        label='Enfermedad', queryset=Enfermedad.objects.all(),
        help_text='Selecciona una enfermedad del catálogo. Puedes agregarla desde Enfermedades si falta.',
    )

    class Meta:
        model = ReglaClasificacion
        fields = ['nombre', 'enfermedad_catalogo', 'categoria', 'tipo', 'patron', 'prioridad', 'activa']
        labels = {'nombre': 'Nombre de la regla', 'categoria': 'Clasificación'}
        help_texts = {'patron': 'Texto que reconocerá la regla. Para palabras clave puedes usar el nombre de la enfermedad.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['enfermedad_catalogo'].initial = Enfermedad.objects.filter(
                clave=clave_enfermedad(self.instance.enfermedad),
            ).first()
        self.fields['enfermedad_catalogo'].empty_label = 'Selecciona una enfermedad'
        self.fields['categoria'].choices = [('', 'Selecciona una categoría'), ('ENO', 'ENO'), ('GES_AUGE', 'GES/AUGE')]
        if not self.instance.pk:
            self.initial.setdefault('tipo', 'PALABRA')
        estilo_formulario(self)

    def clean(self):
        datos = super().clean()
        if datos.get('enfermedad_catalogo'):
            self.instance.enfermedad = datos['enfermedad_catalogo'].nombre
        return datos
