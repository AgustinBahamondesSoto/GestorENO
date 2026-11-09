# Product Backlog de Gestor ENO

Proyecto: sistema de análisis estadístico de datos clínicos a partir de plantillas Excel hospitalarias.

Fuente de requisitos: sección III.1.3 del informe de Evaluación 2 entregado por el equipo. Los dos PDF y el DOCX coinciden en los cinco elementos del backlog. Se mantiene su orden y prioridad. Los criterios de aceptación siguientes concretan esos requisitos para el desarrollo; las decisiones adicionales deben revisarse con la usuaria. El informe utiliza los nombres Product Backlog y Sprint Backlog dentro de una metodología XP.

## Lista priorizada

| ID | Requisito del informe | Prioridad | App Django | Dependencias | Entrega local |
| --- | --- | --- | --- | --- | --- |
| PB-01 | Importación y validación de la planilla Excel | Muy alta | `importaciones` | PB-02 para guardar filas válidas | Carga web, validación y registro de inconsistencias |
| PB-02 | Paciente maestro por RUT e historial de consultas | Muy alta | `pacientes` | Ninguna | RUT validado y único, historial y conflictos |
| PB-03 | Clasificación automática del texto clínico | Alta | `clasificacion` | PB-02 | Motor Strategy y diccionario administrable |
| PB-04 | Indicadores sobre pacientes únicos | Alta | `indicadores` | PB-02, PB-03 | Panel con filtros y conteos por RUT |
| PB-05 | Reportes predefinidos y exportación a Excel | Media | `reportes` | PB-03, PB-04 | Excel con indicadores, ENO pendientes y GES vigentes |

La entrega local está implementada y cuenta con pruebas automatizadas. La estructura de entrada ya se adaptó al CSV hospitalario entregado. La aceptación del diccionario clínico y los formatos de reportes internos del hospital permanece pendiente. No se atribuyen estimaciones ni aprobaciones nuevas a la clienta.

## PB-01 Importación y validación

Como funcionaria, quiero cargar mi planilla Excel y conocer las filas con problemas para reducir la revisión manual.

Criterios de aceptación:

- Aceptar `.xlsx` y validar la presencia de las ocho columnas documentadas antes de guardar registros.
- Informar columnas faltantes o duplicadas y rechazar archivos ilegibles con un mensaje claro.
- Reconocer encabezados con mayúsculas, tildes, espacios o guiones bajos.
- Validar RUT, campos obligatorios, edad, peso y fecha opcional.
- Procesar las filas válidas aunque existan filas inválidas; registrar número de fila Excel y motivo de cada error.
- Mostrar total de filas no vacías, consultas nuevas, pacientes nuevos, filas inválidas y consultas ya importadas.
- Mantener trazabilidad por archivo, usuario, fecha y fila, sin guardar el archivo original en una carpeta pública.

Implementación: `importaciones/services.py`, formularios, vistas y modelos de importación e inconsistencia. CU01, CU02 y CU12.

## PB-02 Paciente maestro e historial

Como funcionaria, quiero que cada paciente exista una sola vez aunque aparezca en varias filas para evitar estadísticas duplicadas.

Criterios de aceptación:

- Normalizar RUT eliminando puntos y espacios, unificando el guion y convirtiendo K a mayúscula.
- Verificar el dígito mediante módulo 11 y rechazar RUT vacíos o inválidos.
- Garantizar unicidad del RUT en la base de datos.
- Conservar cada fila válida nueva como una consulta del paciente correspondiente.
- No duplicar pacientes ni consultas al volver a importar la misma planilla.
- Conservar en el maestro los datos de la consulta más reciente y registrar conflictos de nombre, edad, sexo o previsión.
- Permitir buscar un paciente y consultar su historial con trazabilidad a la importación.

Implementación: `pacientes/models.py`, `validators.py`, `repositories.py` y vistas de pacientes. CU03, CU04 y CU09. Repository encapsula la consulta y creación de pacientes.

## PB-03 Clasificación clínica

Como funcionaria, quiero clasificar los antecedentes y signos vitales para reconocer los casos GES/AUGE y ENO en mis análisis.

Criterios de aceptación:

- Examinar ambos campos de texto mediante estrategias de palabras clave y expresiones regulares.
- Asignar ENO, GES/AUGE o SIN_ANTECEDENTES y conservar las enfermedades y reglas coincidentes.
- Administrar enfermedad, categoría, patrón, prioridad y activación desde Django Admin.
- Validar expresiones regulares al editar el diccionario desde la administración.
- Aplicar primero la regla de menor prioridad numérica cuando hay varias categorías coincidentes; los empates se resuelven por ID.
- Permitir reclasificar el historial después de actualizar el diccionario.

Implementación: `clasificacion/models.py`, `services.py`, administración y comando `reclasificar`. CU05 y CU11.

Pendiente de aceptación de dominio: diccionario autorizado, prioridad entre categorías, tratamiento de negaciones, antecedentes familiares y expresiones ambiguas. SIN_ANTECEDENTES significa que no hubo coincidencias con las reglas activas; no certifica ausencia clínica de enfermedad. No se incluyen reglas clínicas inventadas como si estuvieran validadas.

## PB-04 Indicadores estadísticos

Como funcionaria, quiero consultar indicadores sobre personas únicas para obtener resultados independientes del número de consultas.

Criterios de aceptación:

- Calcular población total por paciente maestro, nunca por número de filas.
- Mostrar prevalencia por enfermedad, distribución por edad, sexo y previsión, y proporción de pacientes con categoría GES/AUGE o ENO.
- Filtrar por edad mínima/máxima, sexo, previsión y categoría; rechazar rangos de edad invertidos.
- Contar cada paciente una sola vez dentro de cada enfermedad o categoría.
- Resolver poblaciones vacías sin división por cero.
- Explicar el denominador y la posibilidad de que una persona figure en varias categorías a lo largo del historial.

Implementación: `indicadores/services.py`, `forms.py` y panel. CU06, CU07 y CU08.

Decisión inicial: los filtros demográficos usan el paciente maestro; la condición clínica y prevalencia consultan todo el historial. El porcentaje es pacientes distintos del grupo / total de pacientes filtrados × 100. Los grupos pueden superponerse; sus porcentajes no necesariamente suman 100. Sin fechas y período de observación completos, estos valores requieren validación antes de interpretarse como indicadores epidemiológicos del establecimiento.

## PB-05 Reportes y exportación

Como funcionaria, quiero descargar mis reportes recurrentes en Excel para utilizarlos en el análisis interno.

Criterios de aceptación:

- Exportar un `.xlsx` descargable con resumen, edad, sexo, previsión, categorías y prevalencia.
- Incluir hojas de pacientes con consultas ENO pendientes de notificación y consultas GES/AUGE con seguimiento vigente.
- Agrupar esas hojas por paciente único e indicar cantidad de consultas y enfermedades detectadas.
- Permitir registrar desde administración la notificación ENO y el cierre o vigencia GES por consulta.
- Respetar los filtros del panel en la descarga y evitar fórmulas provenientes de texto importado.
- Ofrecer una plantilla de entrada vacía.

Implementación: `reportes/services.py`, vistas de descarga y estados de `Consulta`. CU10.

La entrada ya conserva las 14 columnas del CSV de referencia y admite CSV y Excel con títulos previos al encabezado. Pendiente: validar el formato exacto de los reportes de salida. Marcar una notificación en este sistema registra seguimiento interno; no realiza el trámite ante la autoridad sanitaria.

## Primera iteración del informe

Duración prevista: dos semanas. Objetivo: PB-01 y PB-02, incluyendo normalización de RUT.

| Historia del informe | Responsable indicado | Alcance |
| --- | --- | --- |
| HU-01 | Agustín Bahamondes | Importación y validación |
| HU-02 | Matías Cortés | Paciente maestro e historial |
| HU-03 | Omar Castro | Normalización y validación de RUT |
| Pruebas y enlace durante la primera semana | Camilo Sepúlveda | Validación automatizada y coordinación con la clienta |

Estas asignaciones reproducen la planificación del informe; no implican que esas personas hayan ejecutado los cambios de este repositorio. Las pruebas de importación y RUT se incorporaron antes de su implementación y se verificó su fallo inicial.

## Criterios de cierre

- Ejecutar `python manage.py check` y `python manage.py test` sin errores.
- Verificar unicidad por RUT, reimportación, conflictos, filas inválidas y exportación con datos sintéticos.
- Revisar con la usuaria la planilla de referencia y los reportes finales.
- Medir el objetivo del informe de al menos 95 % de acierto clínico con muestras validadas; no se considera demostrado por pruebas sintéticas.
- Medir la cobertura objetivo de al menos 80 % en deduplicación y cálculo y mantener las pruebas al evolucionar las reglas.
