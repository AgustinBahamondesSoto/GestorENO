import re
import unicodedata
from django.db import migrations


def poblar_catalogo(apps, schema_editor):
    Enfermedad = apps.get_model('clasificacion', 'Enfermedad')
    Regla = apps.get_model('clasificacion', 'ReglaClasificacion')
    Consulta = apps.get_model('pacientes', 'Consulta')
    alias = schema_editor.connection.alias

    def registrar(nombre):
        nombre = ' '.join(nombre.split())
        clave = ''.join(c for c in unicodedata.normalize('NFD', nombre.casefold()) if unicodedata.category(c) != 'Mn')
        if not clave or len(nombre) > 150 or clave in {
            'sin antecedentes', 'sin antecedentes morbidos relevantes', 'sin informacion',
            'no aplica', 'ninguna', 'ninguno',
        }:
            return None
        enfermedad, _ = Enfermedad.objects.using(alias).get_or_create(clave=clave, defaults={'nombre': nombre})
        return enfermedad

    for regla in Regla.objects.using(alias).all().iterator():
        registrar(regla.enfermedad)
    for consulta in Consulta.objects.using(alias).all().iterator():
        nombres = re.split(r'[;\n]+', consulta.enfermedades_declaradas) + consulta.enfermedades
        ids = [e.pk for nombre in nombres if (e := registrar(nombre)) is not None]
        consulta.enfermedades_registradas.set(ids)


class Migration(migrations.Migration):
    dependencies = [
        ('pacientes', '0003_consulta_enfermedades_registradas_consulta_usuario_and_more'),
        ('clasificacion', '0002_enfermedad'),
    ]
    operations = [migrations.RunPython(poblar_catalogo, migrations.RunPython.noop)]
