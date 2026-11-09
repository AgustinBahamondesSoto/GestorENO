from io import BytesIO

from django.test import TestCase
from openpyxl import Workbook

from pacientes.models import Paciente, Consulta
from .models import Importacion
from .services import importar_excel, ErrorPlantilla


def planilla(filas, cabecera=None):
    wb = Workbook()
    wb.active.append(cabecera or ['Nombre', 'RUT', 'Edad', 'Peso', 'Sexo', 'Previsión', 'Antecedentes médicos', 'Signos vitales', 'Fecha consulta'])
    for fila in filas:
        wb.active.append(fila)
    archivo = BytesIO()
    wb.save(archivo)
    archivo.seek(0)
    return archivo


FILA = ['Persona de prueba', '12.345.678-5', 30, 65, 'F', 'Fonasa', 'Sin antecedentes', 'Normal', '2026-10-01']


class ImportacionTests(TestCase):
    def test_mismo_rut_un_paciente_y_dos_consultas(self):
        otra = [*FILA]
        otra[1], otra[2], otra[8] = '12345678-5', 31, '2026-10-02'
        lote = importar_excel(planilla([FILA, otra]), 'prueba.xlsx')
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(Consulta.objects.count(), 2)
        self.assertEqual(Paciente.objects.get().edad, 31)
        self.assertEqual(lote.inconsistencias.filter(tipo='CONFLICTO').count(), 1)

    def test_reimportacion_no_duplica_consultas(self):
        importar_excel(planilla([FILA, FILA]), 'primero.xlsx')
        lote = importar_excel(planilla([FILA, FILA]), 'segundo.xlsx')
        self.assertEqual(Consulta.objects.count(), 2)
        self.assertEqual(lote.omitidas, 2)

    def test_filas_invalidas_no_detienen_validas(self):
        mala = [*FILA]
        mala[2] = 'treinta'
        rut_malo = [*FILA]
        rut_malo[1] = '12345678-9'
        lote = importar_excel(planilla([mala, FILA, rut_malo]), 'prueba.xlsx')
        self.assertEqual(lote.invalidas, 2)
        self.assertEqual(lote.validas, 1)
        self.assertEqual(list(lote.inconsistencias.values_list('fila', flat=True)), [2, 4])

    def test_faltan_columnas_no_persiste(self):
        with self.assertRaises(ErrorPlantilla):
            importar_excel(planilla([], ['Nombre', 'RUT']), 'prueba.xlsx')
        self.assertFalse(Importacion.objects.exists())

    def test_archivo_corrupto(self):
        with self.assertRaises(ErrorPlantilla):
            importar_excel(BytesIO(b'no es excel'), 'prueba.xlsx')

    def test_consulta_antigua_no_sobreescribe_maestro(self):
        reciente = [*FILA]
        reciente[2], reciente[8] = 32, '2026-10-20'
        importar_excel(planilla([reciente]), 'reciente.xlsx')
        importar_excel(planilla([FILA]), 'antigua.xlsx')
        self.assertEqual(Paciente.objects.get().edad, 32)

    def test_duplicados_de_columnas_y_extension(self):
        for archivo, nombre in [(planilla([], ['Nombre', 'RUT', 'Edad', 'Peso', 'Sexo', 'Previsión', 'Antecedentes médicos', 'Signos vitales', 'rut']), 'prueba.xlsx'), (planilla([FILA]), 'prueba.xls')]:
            with self.subTest(nombre=nombre), self.assertRaises(ErrorPlantilla):
                importar_excel(archivo, nombre)
        self.assertFalse(Importacion.objects.exists())

    def test_fechas_invalidas_y_campos_vacios(self):
        for indice, valor in [(8, 'ayer'), (0, ''), (3, -20), (2, 30.5)]:
            fila = [*FILA]
            fila[indice] = valor
            with self.subTest(indice=indice):
                lote = importar_excel(planilla([fila, FILA]), 'prueba.xlsx')
                self.assertEqual(lote.invalidas, 1)
        self.assertEqual(Paciente.objects.count(), 1)

    def test_filas_sin_fecha_y_cabeceras_normalizadas(self):
        cabecera = [' NOMBRE ', 'rut', 'EDAD', 'peso', 'sexo', 'PREVISION', 'antecedentes', 'signos_vitales']
        lote = importar_excel(planilla([FILA[:8]], cabecera), 'prueba.xlsx')
        self.assertEqual(lote.validas, 1)
        self.assertIsNone(Consulta.objects.get().fecha)


class PlantillaHospitalTests(TestCase):
    def csv_hospital(self, separador=',', codificacion='utf-8-sig', fila_mala=False):
        import csv
        from io import StringIO
        from .services import PLANTILLA_HOSPITAL
        texto = StringIO(newline='')
        writer = csv.writer(texto, delimiter=separador)
        writer.writerow(['FICHA DE REGISTRO DE PACIENTES - HOSPITAL'])
        writer.writerow(['Instrucciones de la plantilla'])
        writer.writerow([])
        writer.writerow(PLANTILLA_HOSPITAL)
        fila = ['María', 'Pérez', '12.345.678-5', 30, 'Término ficticio alfa', 'Fonasa A', '65,5', 'Femenino', 'Calle ficticia 100, Valdivia', '13-08-2026 - Control de seguimiento', 'Antecedente de prueba', 'PA de prueba', 'Domicilio', 'GES/AUGE y ENO']
        if fila_mala:
            mala = fila[:]
            mala[2] = ''
            writer.writerow(mala)
        writer.writerow(fila)
        writer.writerow([''] * 14)
        writer.writerow(['Total pacientes registrados:', '1'] + [''] * 12)
        return BytesIO(texto.getvalue().encode(codificacion))

    def test_csv_preserva_catorce_columnas_y_no_confunde_condicion(self):
        from datetime import date
        lote = importar_excel(self.csv_hospital(), 'hospital.csv')
        consulta = Consulta.objects.get()
        self.assertEqual(lote.total, 1)
        self.assertEqual(lote.invalidas, 0)
        self.assertEqual(consulta.apellido, 'Pérez')
        self.assertEqual(consulta.paciente.nombre_completo, 'María Pérez')
        self.assertEqual(consulta.fecha, date(2026, 8, 13))
        self.assertEqual(str(consulta.peso), '65.50')
        self.assertEqual(consulta.condicion_declarada, 'GES/AUGE y ENO')
        self.assertEqual(consulta.clasificacion, 'SIN_ANTECEDENTES')
        self.assertEqual(consulta.domicilio_comuna, 'Calle ficticia 100, Valdivia')
        self.assertEqual(consulta.destino, 'Domicilio')
        self.assertEqual(consulta.enfermedades_declaradas, 'Término ficticio alfa')

    def test_csv_windows1252_punto_y_coma_y_fila_real(self):
        lote = importar_excel(self.csv_hospital(';', 'cp1252', fila_mala=True), 'hospital.csv')
        self.assertEqual(lote.validas, 1)
        self.assertEqual(lote.invalidas, 1)
        self.assertEqual(lote.inconsistencias.get().fila, 5)

    def test_excel_con_titulos_y_csv_no_duplican_consultas(self):
        import csv
        texto = self.csv_hospital().read().decode('utf-8-sig')
        libro = Workbook()
        for fila in csv.reader(texto.splitlines()):
            libro.active.append(fila)
        archivo = BytesIO()
        libro.save(archivo)
        archivo.seek(0)
        importar_excel(archivo, 'hospital.xlsx')
        lote = importar_excel(self.csv_hospital(), 'hospital.csv')
        self.assertEqual(lote.omitidas, 1)
        self.assertEqual(Consulta.objects.count(), 1)

    def test_enfermedades_declaradas_alimentan_motor(self):
        from clasificacion.models import ReglaClasificacion
        ReglaClasificacion.objects.create(nombre='Regla de prueba', enfermedad='Alfa de prueba', categoria='ENO', tipo='PALABRA', patron='término ficticio alfa')
        importar_excel(self.csv_hospital(), 'hospital.csv')
        self.assertEqual(Consulta.objects.get().clasificacion, 'ENO')

    def test_csv_binario_rechazado(self):
        with self.assertRaises(ErrorPlantilla):
            importar_excel(BytesIO(b'\x00\x00'), 'hospital.csv')
