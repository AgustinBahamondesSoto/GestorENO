from django import forms


class ImportarForm(forms.Form):
    archivo = forms.FileField(label='Planilla Excel o CSV', widget=forms.ClearableFileInput(attrs={'accept': '.xlsx,.csv', 'class': 'form-control'}))

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.lower().endswith(('.xlsx', '.csv')):
            raise forms.ValidationError('Solo se admiten archivos .xlsx o .csv.')
        if archivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('El tamaño máximo es 10 MB.')
        return archivo
