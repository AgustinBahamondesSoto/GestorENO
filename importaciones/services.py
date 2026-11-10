from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import csv
from io import StringIO
import re
from pathlib import Path
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

from django.core.exceptions import ValidationError
from django.db import transaction
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from clasificacion.services import MotorReconocimiento, simplificar
from clasificacion.catalogo import sincronizar_enfermedades
from pacientes.models import Consulta
from pacientes.repositories import RepositorioDjango
from pacientes.validators import normalizar_rut
from .models import Importacion, Inconsistencia, EstadoPacienteImportacion

CAMPOS_MAESTRO = ('nombre', 'apellido', 'domicilio_comuna', 'edad', 'sexo', 'prevision')


COLUMNAS = ('nombre', 'rut', 'edad', 'peso', 'sexo', 'prevision', 'antecedentes medicos', 'signos vitales')
ALIASES = {
    'antecedentes': 'antecedentes medicos', 'fecha': 'fecha consulta',
    'peso (kg)': 'peso', 'signos vitales (ultimos examenes)': 'signos vitales',
    'enfermedades cronicas / complicaciones (listado)': 'enfermedades_declaradas',
    'domicilio y comuna': 'domicilio_comuna', 'ultimas consultas': 'ultimas_consultas',
    'destino del paciente': 'destino',
    'condicion del problema (ges/auge - eno)': 'condicion_declarada',
}
EXTRAS = ('apellido', 'domicilio_comuna', 'enfermedades_declaradas', 'ultimas_consultas', 'destino', 'condicion_declarada')
PLANTILLA_HOSPITAL = [
    'Nombre', 'Apellido', 'RUT', 'Edad', 'Enfermedades crónicas / Complicaciones (listado)',
    'Previsión', 'Peso (kg)', 'Sexo', 'Domicilio y comuna', 'Últimas consultas',
    'Antecedentes médicos', 'Signos vitales (últimos exámenes)', 'Destino del paciente',
    'Condición del Problema (GES/AUGE - ENO)',
]


class ErrorPlantilla(ValueError):
    pass


def encabezado(valor):
    texto = ' '.join(simplificar(str(valor or '')).replace('_', ' ').split())
    return ALIASES.get(texto, texto)


def validar_fila(datos):
    for campo in ('nombre', 'rut', 'edad', 'peso', 'sexo', 'prevision'):
        if datos.get(campo) is None or not str(datos[campo]).strip():
            raise ValidationError(f'Campo obligatorio vacío: {campo}.')
    rut = normalizar_rut(datos['rut'])
    try:
        edad = Decimal(str(datos['edad']))
        peso = Decimal(str(datos['peso']).replace(',', '.'))
        if not edad.is_finite() or edad != edad.to_integral_value() or not 0 <= edad <= 130:
            raise ValueError
        if not peso.is_finite() or not 0 < peso <= Decimal('9999.99') or peso != peso.quantize(Decimal('.01')):
            raise ValueError
    except (ValueError, InvalidOperation):
        raise ValidationError('Edad inválida (entero entre 0 y 130) o peso inválido (positivo, hasta 2 decimales).')
    fecha = datos.get('fecha consulta')
    if not fecha and datos.get('ultimas_consultas'):
        coincidencia = re.match(r'^\s*(\d{2}-\d{2}-\d{4})(?:\s|$)', str(datos['ultimas_consultas']))
        if coincidencia:
            try:
                fecha = datetime.strptime(coincidencia[1], '%d-%m-%Y').date()
            except ValueError:
                raise ValidationError('Fecha inválida en Últimas consultas; use DD-MM-AAAA al inicio.')
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    elif fecha not in (None, '') and not isinstance(fecha, date):
        try:
            fecha = date.fromisoformat(str(fecha).strip())
        except ValueError:
            raise ValidationError('Fecha de consulta inválida: use una fecha Excel o AAAA-MM-DD.')
    campos = {k: str(datos[k]).strip() for k in ('nombre', 'sexo', 'prevision')}
    for campo, limite in (('nombre', 200), ('sexo', 30), ('prevision', 100)):
        if len(campos[campo]) > limite:
            raise ValidationError(f'{campo}: máximo {limite} caracteres.')
    campos['sexo'] = {'femenino': 'F', 'f': 'F', 'masculino': 'M', 'm': 'M', 'otro': 'Otro'}.get(simplificar(campos['sexo']), campos['sexo'])
    extras = {k: str(datos.get(k) or '').strip() for k in EXTRAS}
    for campo, limite in [('apellido', 200), ('domicilio_comuna', 300), ('destino', 200), ('condicion_declarada', 100)]:
        if len(extras[campo]) > limite:
            raise ValidationError(f'{campo}: máximo {limite} caracteres.')
    return {
        **campos, **extras, 'rut': rut, 'edad': int(edad), 'peso': str(peso.quantize(Decimal('.01'))), 'fecha': fecha or None,
        'antecedentes': str(datos.get('antecedentes medicos') or '').strip(),
        'signos_vitales': str(datos.get('signos vitales') or '').strip(),
    }


def importar_excel(archivo, nombre, usuario=None, repositorio=None):
    extension = Path(nombre).suffix.lower()
    if extension not in ('.xlsx', '.csv'):
        raise ErrorPlantilla('Seleccione un archivo .xlsx o .csv.')
    if getattr(archivo, 'size', 0) > 10 * 1024 * 1024:
        raise ErrorPlantilla('El archivo excede el máximo de 10 MB.')
    if extension == '.csv':
        contenido = archivo.read(10 * 1024 * 1024 + 1)
        if len(contenido) > 10 * 1024 * 1024:
            raise ErrorPlantilla('El archivo excede el máximo de 10 MB.')
        try:
            texto = contenido.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                texto = contenido.decode('cp1252')
            except UnicodeDecodeError as exc:
                raise ErrorPlantilla('Codificación CSV no reconocida. Use UTF-8 o Windows-1252.') from exc
        if '\x00' in texto:
            raise ErrorPlantilla('El archivo CSV contiene datos ilegibles.')
        linea = next((l for l in texto.splitlines()[:20] if 'rut' in l.casefold() and 'nombre' in l.casefold()), '')
        separador = ';' if linea.count(';') > linea.count(',') else ','
        lector = csv.reader(StringIO(texto, newline=''), delimiter=separador, strict=True)
        try:
            return _procesar_filas(enumerate(lector, start=1), nombre, usuario, repositorio or RepositorioDjango())
        except csv.Error as exc:
            raise ErrorPlantilla('El CSV contiene filas mal formadas. Revise las comillas y separadores.') from exc
    try:
        libro = load_workbook(archivo, read_only=True, data_only=False)
    except (BadZipFile, InvalidFileException, OSError, ValueError, KeyError, ParseError) as exc:
        raise ErrorPlantilla('No se pudo leer el archivo. Compruebe que sea un Excel .xlsx válido.') from exc
    try:
        return _procesar(libro, nombre, usuario, repositorio or RepositorioDjango())
    except (BadZipFile, InvalidFileException, OSError, KeyError, ParseError) as exc:
        raise ErrorPlantilla('La planilla contiene datos ilegibles o está dañada. No se guardó esta importación.') from exc
    finally:
        libro.close()


def _procesar(libro, nombre, usuario, repositorio):
    hoja = libro.worksheets[0]
    return _procesar_filas(enumerate(hoja.iter_rows(values_only=True), start=1), nombre, usuario, repositorio)


@transaction.atomic
def _procesar_filas(filas, nombre, usuario, repositorio):
    titulos = []
    fila_cabecera = 0
    for numero, valores in filas:
        candidatos = [encabezado(c) for c in valores]
        if 'rut' in candidatos and 'nombre' in candidatos:
            titulos, fila_cabecera = candidatos, numero
            break
        if numero >= 20:
            break
    faltantes = set(COLUMNAS) - set(titulos)
    if faltantes:
        raise ErrorPlantilla('Faltan columnas obligatorias: ' + ', '.join(sorted(faltantes)))
    no_vacios = [t for t in titulos if t]
    if len(set(no_vacios)) != len(no_vacios):
        raise ErrorPlantilla('La cabecera contiene columnas duplicadas.')
    lote = Importacion.objects.create(archivo=Path(nombre).name[:255], usuario=usuario)
    motor = MotorReconocimiento()
    repeticiones = Counter()
    for numero, valores in filas:
        if all(v is None or v == '' for v in valores):
            continue
        # El resumen al pie de la plantilla no es un registro de paciente.
        if (valores and encabezado(valores[0]).rstrip(':') == 'total pacientes registrados'
                and all(v is None or v == '' for v in valores[2:])):
            continue
        if numero - fila_cabecera > 50000:
            raise ErrorPlantilla('La planilla supera el máximo de 50.000 filas.')
        lote.total += 1
        try:
            datos = validar_fila(dict(zip(titulos, valores)))
        except ValidationError as exc:
            lote.invalidas += 1
            Inconsistencia.objects.create(importacion=lote, fila=numero, tipo='ERROR', motivo='; '.join(exc.messages))
            continue
        firma = json.dumps({k: v for k, v in datos.items() if k not in EXTRAS or v}, sort_keys=True, default=str, ensure_ascii=False)
        repeticiones[firma] += 1
        huella = sha256(f'{firma}|{repeticiones[firma]}'.encode()).hexdigest()
        if Consulta.objects.filter(huella=huella).exists():
            lote.omitidas += 1
            continue
        maestro = {k: datos[k] for k in ('nombre', 'apellido', 'domicilio_comuna', 'edad', 'sexo', 'prevision')}
        paciente, creado = repositorio.obtener_o_crear(datos['rut'], maestro)
        estado, _ = EstadoPacienteImportacion.objects.get_or_create(
            importacion=lote, paciente=paciente,
            defaults={'antes': {} if creado else {k: getattr(paciente, k) for k in CAMPOS_MAESTRO}},
        )
        lote.pacientes_nuevos += int(creado)
        anterior = paciente.consultas.order_by('-fecha', '-registrada', '-pk').first()
        if not creado:
            cambios = [k for k, v in maestro.items() if getattr(paciente, k) != v]
            if cambios:
                Inconsistencia.objects.create(importacion=lote, fila=numero, tipo='CONFLICTO', motivo='Datos personales distintos en: ' + ', '.join(cambios) + '. Se conserva en el maestro la consulta con fecha más reciente; sin fechas, el orden de importación.')
            if anterior is None or (datos['fecha'] or date.min) >= (anterior.fecha or date.min):
                for k, v in maestro.items():
                    setattr(paciente, k, v)
                paciente.save()
        estado.despues = {k: getattr(paciente, k) for k in CAMPOS_MAESTRO}
        estado.save(update_fields=['despues'])
        resultado = motor.clasificar(datos['antecedentes'], datos['signos_vitales'], datos['enfermedades_declaradas'])
        campos = {k: v for k, v in datos.items() if k != 'rut'}
        consulta = Consulta.objects.create(paciente=paciente, importacion=lote, fila=numero, huella=huella, **campos, **resultado, ges_vigente=resultado['clasificacion'] == 'GES_AUGE')
        sincronizar_enfermedades(consulta)
        lote.validas += 1
    lote.save()
    return lote
