# Gestor ENO

Aplicación Django para importar registros clínicos desde Excel, consolidar pacientes por RUT, aplicar reglas de clasificación y exportar estadísticas. Implementa una primera versión de los cinco requisitos del Product Backlog del informe de Evaluación 2.

El backlog, criterios de aceptación y asuntos pendientes de validación están en [docs/PRODUCT_BACKLOG.md](docs/PRODUCT_BACKLOG.md).

## Ejecutar en Windows PowerShell

El entorno `.venv` existente se conservó y se utilizó para crear el proyecto y las apps. Además de Django, se instaló `openpyxl` para manejar `.xlsx`.

```powershell
cd GestorENO
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Si PowerShell impide activar el entorno, utiliza directamente `.\.venv\Scripts\python.exe` en lugar de `python`.

Abrir http://127.0.0.1:8000/ e ingresar con el usuario creado. La base SQLite local ya tiene las migraciones aplicadas. No se creó una cuenta con contraseña predeterminada.

## Flujo de trabajo

1. Iniciar sesión y entrar a **Enfermedades** para consultar el catálogo y crear las reglas acordadas con la responsable del diccionario. Cada regla guardada reclasifica el historial automáticamente.
2. Entrar a **Importar planilla** para cargar Excel o CSV y revisar inconsistencias. La importación amplía el catálogo de enfermedades conocidas.
3. Desde **Pacientes**, registrar personas, editar su ficha o agregar y corregir atenciones y enfermedades. Los cambios manuales quedan auditados.
4. En **Indicadores**, filtrar por enfermedad, categoría, edad, sexo y previsión. La tabla identifica a cada paciente por nombre y RUT e informa su clasificación.
5. Descargar el Excel con los filtros aplicados y la hoja **Pacientes filtrados**.
6. Para retirar una carga, usar **Importar planilla → Eliminar última importación**, revisar el alcance y confirmar. Se borran sus consultas y pacientes exclusivos, conservando otros registros y restaurando los datos previos disponibles.

Hay un [archivo de prueba con 50 pacientes de Los Ríos](outputs/los_rios_50/plantilla_pacientes_Los_Rios_50.xlsx): 20 de la plantilla Valdivia con una nueva atención y 30 nuevos. Todos tienen domicilio ficticio en Valdivia, Región de Los Ríos. La guía incluye el ciclo de carga, eliminación y recarga.

Consultar [la guía de operación](docs/GUIA_DE_USO.md) para los procedimientos, decisiones de clasificación y actualización de una instalación existente. Todas estas funciones están disponibles para usuarios autenticados; no requieren ser staff ni entrar a Django Admin. La administración se conserva para tareas técnicas y actualización de estados de seguimiento.

## Estructura

| Carpeta | Responsabilidad |
| --- | --- |
| `gestor_eno` | Configuración del proyecto y rutas |
| `importaciones` | Carga Excel, validación, lotes e inconsistencias |
| `pacientes` | RUT, paciente maestro, consultas y Repository |
| `clasificacion` | Diccionario, estrategias de clasificación y reclasificación |
| `indicadores` | Filtros y estadísticas por paciente único |
| `reportes` | Plantilla y exportación Excel |
| `templates`, `static` | Interfaz web en español |
| `docs` | Backlog y criterios de aceptación |

El proyecto se generó con `django-admin startproject gestor_eno .` y las apps con `python manage.py startapp <nombre>`.

## Formato de entrada

Se usa la plantilla hospitalaria de 14 columnas: Nombre, Apellido, RUT, Edad, Enfermedades crónicas / Complicaciones (listado), Previsión, Peso (kg), Sexo, Domicilio y comuna, Últimas consultas, Antecedentes médicos, Signos vitales (últimos exámenes), Destino del paciente y Condición del Problema (GES/AUGE - ENO).

Se admiten Excel `.xlsx` (primera hoja) y CSV, con encabezados dentro de las primeras 20 filas. CSV acepta UTF-8 o Windows-1252 y separadores coma o punto y coma. Las filas de título y el resumen final de la plantilla se reconocen sin crear pacientes. También se admite el formato anterior de ocho columnas.

Nombre, RUT, edad, peso, sexo y previsión son obligatorios. Las columnas de antecedentes y signos vitales deben existir, pero su texto puede estar vacío. Edad admite enteros entre 0 y 130; peso, valores positivos con hasta dos decimales. Se extrae la fecha DD-MM-AAAA al inicio de Últimas consultas, o se usa una columna explícita opcional Fecha consulta con una fecha Excel o AAAA-MM-DD.

Los campos adicionales se conservan en el historial. La condición declarada en la planilla se muestra separada de la clasificación automática. Las enfermedades declaradas se incorporan al catálogo sin asignarles una categoría por defecto. El límite de archivo sigue siendo 10 MB y 50.000 filas.

Se preparó una [copia Excel con datos ficticios](outputs/plantilla_demo/plantilla_pacientes_ficticios.xlsx), con ajustes de coherencia documentados en [docs/PLANTILLA_DEMO.md](docs/PLANTILLA_DEMO.md). El CSV original se conservó y las comprobaciones no dejaron datos de demostración cargados en la base.

## Interfaz con Bootstrap

La interfaz usa Bootstrap 5.3.8 guardado en `static/vendor/bootstrap`, con navegación plegable en móvil, cuadrícula adaptable, tarjetas, tablas, formularios y alertas. Conserva la paleta del diseño inicial y funciona sin conexión a un CDN. `static/app.css` contiene únicamente el tema visual del proyecto.

## Decisiones de datos

- El RUT canónico tiene formato `12345678-5`, con restricción única en base de datos.
- Cada consulta conserva nombre, edad, peso, sexo y previsión de su fila original. El maestro conserva los datos de la fecha más reciente; los empates se resuelven por orden de importación. Una fecha conocida tiene preferencia sobre una consulta sin fecha. Los conflictos se registran por campo.
- La huella de una consulta utiliza el RUT normalizado, datos de la fila, fecha y posición relativa entre filas idénticas. Esto conserva filas repetidas dentro de una planilla y omite su repetición al reimportarla. Si dos atenciones reales tienen todos los campos idénticos y no existe fecha o identificador de consulta que las distinga, no es posible diferenciarlas entre archivos. La planilla real debe aportar ese identificador para resolver ese caso.
- Cambiar datos de una consulta en otra planilla crea una consulta nueva; no sobrescribe el historial.
- No se cargan reglas clínicas de ejemplo en la base de uso. Sin reglas coincidentes se guarda SIN_ANTECEDENTES y la interfaz avisa si no hay diccionario activo. Esta categoría no certifica ausencia de enfermedad.
- Las palabras clave ignoran tildes y mayúsculas y respetan límites de palabra. Las expresiones regulares ignoran mayúsculas y se aplican sobre el texto original. Las reglas se ordenan por prioridad ascendente e ID. La primera coincidencia determina la categoría y todas las coincidencias aportan enfermedades y trazabilidad.
- El motor inicial no interpreta por sí solo negaciones, contexto familiar ni ambigüedad. El diccionario y sus resultados requieren aceptación de dominio; no se afirma cumplir el 95 % de acierto del informe.
- Los indicadores se recalculan sobre los datos actuales. Los filtros clínicos seleccionan atenciones que cumplen la enfermedad y la categoría en el mismo registro. Los porcentajes usan pacientes distintos por grupo sobre la población filtrada. Una persona puede pertenecer a categorías distintas en consultas distintas, por lo que esos porcentajes pueden superponerse.
- ENO nuevas quedan pendientes de notificación; GES nuevas quedan vigentes. Sus estados se actualizan manualmente desde administración. No existe envío automático a organismos externos.
- El reporte exportado contiene datos actuales en nueve hojas, incluida Pacientes filtrados. El formato de entrada ya coincide con las columnas recibidas; el diseño de los reportes de salida aún requiere la referencia del hospital.

## Verificación

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Las pruebas usan datos sintéticos y una base de datos temporal. Cubren validación del RUT, unicidad, reimportación, errores por fila, conflictos de datos, reglas, filtros, indicadores, estados de reportes, exportación, acceso autenticado y CSRF.

## Configuración local

La configuración predeterminada es para desarrollo local, con idioma `es-cl`, zona `America/Santiago` y SQLite. Las variables disponibles son `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS` (lista separada por comas). Si no se define una clave se genera una temporal, por lo que las sesiones se invalidan al reiniciar el proceso. Define una clave propia estable en tu entorno para conservarlas.

Los archivos clínicos originales no se almacenan; sus datos importados sí quedan en SQLite. `.gitignore` excluye la base, el entorno virtual y archivos `.env`. La puesta en producción y la aceptación con datos reales quedan fuera de esta configuración inicial.
