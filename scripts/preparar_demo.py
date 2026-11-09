"""Prepara los datos de demostración sin modificar el CSV original."""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
import re
import argparse

RAIZ = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archivo', type=Path, help='CSV de la plantilla hospitalaria en Windows-1252')
ORIGEN = parser.parse_args().archivo
DESTINO = RAIZ / 'tmp' / 'plantilla_demo'
DESTINO.mkdir(parents=True, exist_ok=True)
filas = list(csv.reader(ORIGEN.read_text(encoding='cp1252').splitlines()))
cabecera = filas[3]
registros = [r[:] for r in filas[4:] if r[2].strip()]
cambios = []


def rut_valido(valor):
    cuerpo = re.sub(r'[^0-9]', '', valor.split('-')[0])
    suma = sum(int(n) * (2 + i % 6) for i, n in enumerate(reversed(cuerpo)))
    dv = 11 - suma % 11
    return f'{int(cuerpo)}-' + ('0' if dv == 11 else 'K' if dv == 10 else str(dv))


identidades = {}
for indice, fila in enumerate(registros, 5):
    original = fila[:]
    enfermedad = fila[4].casefold()
    edad = int(fila[3])
    minimo = re.search(r'(?:personas (?:de|mayores de)|desde) (\d+) a', enfermedad)
    if minimo:
        edad = max(edad, int(minimo[1]))
    if 'menores de 15' in enfermedad:
        edad = min(max(edad, 1), 14)
    if 'displasia luxante de caderas' in enfermedad:
        edad = 1
    fila[3] = edad
    if any(t in enfermedad for t in ('cervicouterino', 'ovario')):
        fila[7] = 'Femenino'
        if original[7] != fila[7]:
            fila[0] = 'Daniela'
    if 'próstata' in enfermedad:
        fila[7] = 'Masculino'
        if original[7] != fila[7]:
            fila[0] = 'Daniel'
    # Solo se corrige el dígito de control: no se presenta este RUT como identidad real.
    fila[2] = rut_valido(fila[2])
    if fila[2] in identidades:
        previo = identidades[fila[2]]
        for columna in (0, 1, 3, 5, 7, 8):
            fila[columna] = previo[columna]
    else:
        identidades[fila[2]] = fila
    edad = int(fila[3])
    fila[6] = round(9 + edad * 2.6, 1) if edad < 15 else float(fila[6])
    fecha = datetime.strptime(fila[9][:10], '%d-%m-%Y')
    fila[9] = fecha.strftime('%d-%m-%Y') + (' - Control pediátrico' if edad < 15 else ' - Control de seguimiento')
    fila[10] = 'Registro ficticio de demostración. Antecedentes declarados: ' + fila[4] + '. Condición indicada para pruebas: ' + fila[13] + '.'
    fila[11] = re.sub(r'\(\d{2}-\d{2}-\d{4}\)', '(' + fecha.strftime('%d-%m-%Y') + ')', fila[11])
    for columna, (antes, despues) in enumerate(zip(original, fila)):
        if str(antes) != str(despues):
            cambios.append({'fila_original': indice, 'columna': cabecera[columna], 'antes': antes, 'despues': despues})

matriz = [
    ['FICHA DE REGISTRO DE PACIENTES - DATOS FICTICIOS'] + [''] * 13,
    ['Datos de demostración para pruebas de software. Categorías declaradas sin validación normativa.'] + [''] * 13,
    [''] * 14, cabecera, *registros,
]
(DESTINO / 'datos.json').write_text(json.dumps(matriz, ensure_ascii=False), encoding='utf-8')
(DESTINO / 'cambios.json').write_text(json.dumps(cambios, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'registros': len(registros), 'pacientes_por_rut': len(identidades), 'cambios_por_columna': dict(Counter(c['columna'] for c in cambios))}, ensure_ascii=False))
