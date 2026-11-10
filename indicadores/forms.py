from django import forms
from pacientes.models import Paciente
from clasificacion.models import Enfermedad


class FiltrosForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        etiquetas_sexo = {'f': 'Femenino', 'm': 'Masculino'}
        for nombre, opcion_todos in [('sexo', 'Todos'), ('prevision', 'Todas')]:
            valores = (
                Paciente.objects.exclude(**{nombre: ''})
                .order_by(nombre)
                .values_list(nombre, flat=True)
                .distinct()
            )
            opciones = {}
            for valor in valores:
                clave = valor.casefold()
                etiqueta = etiquetas_sexo.get(clave, valor) if nombre == 'sexo' else valor
                opciones.setdefault(clave, (valor, etiqueta))
            self.fields[nombre].choices = [('', opcion_todos), *opciones.values()]
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'

    edad_min = forms.IntegerField(label='Edad desde', min_value=0, max_value=130, required=False)
    edad_max = forms.IntegerField(label='Edad hasta', min_value=0, max_value=130, required=False)
    sexo = forms.ChoiceField(label='Sexo', required=False)
    prevision = forms.ChoiceField(label='Previsión', required=False)
    categoria = forms.ChoiceField(label='Categoría', required=False, choices=[('', 'Todas'), ('ENO', 'ENO'), ('GES_AUGE', 'GES/AUGE'), ('SIN_ANTECEDENTES', 'Sin coincidencias')])
    enfermedad = forms.ModelChoiceField(
        label='Enfermedad', queryset=Enfermedad.objects.all(),
        required=False, empty_label='Todas las enfermedades',
    )

    def clean(self):
        datos = super().clean()
        if datos.get('edad_min') is not None and datos.get('edad_max') is not None and datos['edad_min'] > datos['edad_max']:
            raise forms.ValidationError('La edad mínima no puede superar la máxima.')
        return datos
