import json

from cryptography.fernet import InvalidToken
from django.db import migrations

from pacientes.campos import JSONCifrado, TextoCifrado
from pacientes.cifrado import cifrar_texto, descifrar_texto


PREFIJO = 'eno:v1:'
CAMPOS_TEXTO = (
    'antecedentes',
    'signos_vitales',
    'enfermedades_declaradas',
    'ultimas_consultas',
)


def convertir_texto(valor, inversa):
    if valor is None:
        return None
    if inversa:
        if not isinstance(valor, str) or not valor.startswith(PREFIJO):
            raise InvalidToken('El registro no tiene el formato cifrado esperado.')
        return descifrar_texto(valor[len(PREFIJO):])
    return PREFIJO + cifrar_texto(valor)


def convertir_registros(apps, schema_editor, inversa=False):
    # Los modelos históricos siguen teniendo campos normales en este punto.
    Consulta = apps.get_model('pacientes', 'Consulta')
    Cambio = apps.get_model('pacientes', 'CambioPaciente')
    alias = schema_editor.connection.alias

    consultas = Consulta.objects.using(alias).order_by('pk')
    for fila in consultas.values('pk', *CAMPOS_TEXTO).iterator(chunk_size=200):
        cambios = {
            campo: convertir_texto(fila[campo], inversa)
            for campo in CAMPOS_TEXTO
        }
        Consulta.objects.using(alias).filter(pk=fila['pk']).update(**cambios)

    historial = Cambio.objects.using(alias).order_by('pk')
    for fila in historial.values('pk', 'antes', 'despues').iterator(chunk_size=200):
        cambios = {}
        for campo in ('antes', 'despues'):
            if inversa:
                cambios[campo] = json.loads(convertir_texto(fila[campo], True))
            else:
                texto = json.dumps(fila[campo], ensure_ascii=False)
                # Se guarda un token como cadena JSON, conservando JSON válido.
                cambios[campo] = convertir_texto(texto, False)
        Cambio.objects.using(alias).filter(pk=fila['pk']).update(**cambios)


def cifrar_existentes(apps, schema_editor):
    convertir_registros(apps, schema_editor)


def descifrar_existentes(apps, schema_editor):
    convertir_registros(apps, schema_editor, inversa=True)


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('pacientes', '0004_catalogo_historico'),
    ]

    operations = [
        # Primero convertir los valores; después cambiar el estado de los campos.
        migrations.RunPython(cifrar_existentes, descifrar_existentes),
        migrations.AlterField(
            model_name='consulta',
            name='antecedentes',
            field=TextoCifrado(blank=True),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='signos_vitales',
            field=TextoCifrado(blank=True),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='enfermedades_declaradas',
            field=TextoCifrado(
                'enfermedades crónicas o complicaciones de la planilla',
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name='consulta',
            name='ultimas_consultas',
            field=TextoCifrado('últimas consultas de la planilla', blank=True),
        ),
        migrations.AlterField(
            model_name='cambiopaciente',
            name='antes',
            field=JSONCifrado(default=dict),
        ),
        migrations.AlterField(
            model_name='cambiopaciente',
            name='despues',
            field=JSONCifrado(default=dict),
        ),
    ]
