# Guía de operación de Gestor ENO

Esta guía describe las funciones incorporadas tras la revisión del proyecto. Los formularios requieren iniciar sesión; no es necesario entrar a Django Admin ni ejecutar comandos para operar enfermedades, reglas, pacientes o atenciones.

## Enfermedades y reglas de clasificación

El menú **Enfermedades** muestra el catálogo completo de términos conocidos por el sistema, con búsqueda y paginación. Se alimenta de las enfermedades declaradas en planillas, las coincidencias del motor, las reglas existentes al actualizar la aplicación y las incorporaciones manuales. No representa una lista normativa universal.

Los diagnósticos de una celda se separan por punto y coma o salto de línea. Las comas se conservan porque pueden ser parte de un diagnóstico, por ejemplo una descripción con un intervalo de edad. Se omiten expresiones como «No aplica» o «Sin antecedentes mórbidos relevantes». Los nombres se unifican ignorando tildes, mayúsculas y espacios repetidos.

Para agregar una enfermedad:

1. Entrar a **Enfermedades → Agregar enfermedad**.
2. Escribir el nombre y guardar. Los duplicados se informan en el formulario.
3. Se abre el formulario de regla con la enfermedad seleccionada. También se puede cancelar y configurar su regla más adelante.

Para crear una regla:

1. Pulsar **Crear regla de clasificación** desde Indicadores, o **Crear regla** desde el catálogo.
2. Seleccionar la enfermedad y la categoría GES/AUGE o ENO que haya definido la persona responsable del diccionario.
3. Elegir palabra clave o expresión regular y escribir el patrón. Al crear desde una fila del catálogo se propone el nombre de la enfermedad como patrón.
4. Definir prioridad y estado activo. Un número de prioridad menor se evalúa antes. En empates se utiliza el ID de la regla.
5. Guardar. Se actualiza todo el historial automáticamente y se informa cuántas consultas se procesaron.

Para modificar una regla, seleccionar su nombre en el catálogo. Se pueden corregir patrón, categoría y prioridad, o desmarcar **Activa**. Al guardar se recalculan las clasificaciones, incluso cuando se desactiva la última regla. **Actualizar clasificaciones** permite repetir el proceso desde la web.

La actualización es transaccional: si falla el procesamiento, no queda guardada una regla nueva con un historial parcialmente actualizado. La operación se ejecuta en la misma petición y puede tardar con historiales grandes.

El motor analiza enfermedades declaradas, antecedentes y signos vitales. La primera coincidencia determina la categoría principal de cada atención; se conservan todas las enfermedades y reglas coincidentes. Una persona puede tener categorías diferentes en atenciones distintas. Las notificaciones y seguimientos ya registrados se conservan mientras no cambie la categoría. Al cambiar de categoría se reinicia la notificación y la vigencia se habilita únicamente cuando pasa a GES/AUGE.

Una enfermedad agregada sin regla queda registrada y puede filtrarse, pero su atención aparece como **Sin coincidencias** hasta que una regla activa la reconozca. Los nombres y las categorías declaradas en las planillas ficticias no se convierten automáticamente en reglas autorizadas. Las reglas siguen requiriendo validación de dominio; el motor de palabras clave no interpreta por sí mismo negaciones ni contexto familiar.

## Registrar y corregir pacientes

1. Entrar a **Pacientes → Registrar paciente**.
2. Completar RUT, nombres, edad, sexo y previsión; agregar apellidos y domicilio cuando se disponga de ellos.
3. Guardar. El RUT se normaliza y se valida por módulo 11. No se permite registrar otro paciente con el mismo RUT canónico.
4. Desde la ficha, pulsar **Editar paciente** para corregir los datos personales.

Las correcciones actualizan el maestro que utilizan los filtros demográficos. Se guarda el usuario, la fecha y los valores anteriores y nuevos en `CambioPaciente`. Las consultas anteriores mantienen sus datos demográficos originales; no se reescribe el historial al corregir la ficha.

No se fusionan identidades automáticamente. Si se corrige un RUT, las futuras planillas deben usar el RUT corregido para asociarse al mismo paciente. La base de datos impide asignar a la ficha el RUT de otro paciente existente.

## Añadir una enfermedad y ver su clasificación

1. Buscar al paciente y abrir su ficha desde el RUT.
2. Pulsar **Agregar enfermedad o atención**.
3. Indicar la fecha y seleccionar una o más enfermedades del catálogo. Para seleccionar varias en escritorio puede usarse Ctrl o Cmd.
4. Si falta una enfermedad, escribirla en **Otra enfermedad**; se incorpora al catálogo al guardar.
5. Registrar antecedentes, signos vitales, peso y destino cuando estén disponibles. El peso no es obligatorio en un registro manual; la importación mantiene sus validaciones originales.
6. Pulsar **Guardar y clasificar**. Se muestra el resultado y aparece la nueva atención en el historial.

Cada atención manual tiene un identificador propio, usuario y fecha de registro, y no se presenta como si proviniera de un archivo importado. Agregar una atención conserva las anteriores y no incrementa el número de pacientes únicos.

Si se requiere corregir un dato clínico, pulsar **Corregir datos de esta atención**. Se actualizan los datos de esa atención y su clasificación, registrando los valores anteriores y nuevos. Si procedía de Excel o CSV, se mantienen la referencia al lote, la fila y la huella original. Reimportar el mismo archivo no sobrescribe esa corrección ni crea una consulta duplicada.

La ficha muestra los últimos quince eventos de edición con fecha y usuario. El detalle de valores se conserva en la auditoría de la base de datos.

## Filtrar por enfermedad e identificar a los pacientes

En **Indicadores**, seleccionar edad, sexo, previsión, categoría y/o enfermedad, y pulsar **Aplicar filtros**.

- Los filtros demográficos utilizan la ficha actual del paciente.
- Enfermedad se selecciona desde el catálogo y se compara por su identificador, no por fragmentos de texto.
- Cuando se seleccionan enfermedad y categoría, una misma atención debe satisfacer ambas condiciones.
- Los resultados muestran una fila por paciente: nombre completo, RUT, enfermedades registradas y clasificación de las atenciones que cumplen los filtros.
- El RUT enlaza a la ficha y la paginación conserva los filtros.
- Los indicadores se calculan sobre pacientes únicos y sobre las atenciones que cumplen los filtros clínicos. Cada enfermedad se cuenta una sola vez por persona; las categorías y enfermedades pueden superponerse.
- Los pacientes recién creados, sin atenciones, aparecen como **Sin atenciones** cuando no hay filtros clínicos. No aparecen al exigir una enfermedad o categoría.

**Descargar Excel** conserva los filtros y agrega la hoja **Pacientes filtrados**, con nombre, RUT, enfermedades y clasificación. También respeta esos filtros en los reportes de ENO pendientes y GES vigentes. La descarga incluye todos los resultados, no solamente la página visible.

## Actualizar una instalación existente

Después de obtener el código actualizado, ejecutar una sola vez:

```powershell
python manage.py migrate
```

Las migraciones crean el catálogo, las relaciones de enfermedades y la auditoría, y relacionan los términos de consultas y reglas ya existentes. Conservan pacientes, consultas y archivos de referencia. No cambian el texto de acceso ni la plantilla `outputs/plantilla_demo/plantilla_pacientes_Valdivia.xlsx` aportados por el equipo.

El comando `python manage.py reclasificar` permanece disponible para mantenimiento; el flujo cotidiano de la web no depende de él.

## Eliminar la última importación

1. Entrar a **Importar planilla** y pulsar **Eliminar última importación**. También existe el botón en el detalle de la carga más reciente.
2. Revisar el nombre del archivo y la cantidad de consultas, inconsistencias, pacientes exclusivos y pacientes que se conservarán.
3. Marcar la confirmación y pulsar **Eliminar importación y sus datos**. Abrir la pantalla por sí solo no borra información.

Se eliminan las consultas de ese lote, sus asociaciones con enfermedades, su informe de inconsistencias y las fichas creadas únicamente por esa carga. Se conservan las consultas de otras importaciones, las atenciones manuales, las fichas preexistentes y las gestionadas manualmente. El catálogo de enfermedades y las reglas no se eliminan.

En cargas nuevas, el sistema guarda los datos del paciente antes y después de cada lote para recuperar el estado anterior de la ficha. Al eliminar, solo restaura los campos que todavía coinciden con lo dejado por esa carga, de modo que una corrección posterior se conserve. Para importaciones históricas sin esa información, utiliza los datos de las consultas restantes cuando estén disponibles. El RUT no se cambia durante esta recuperación.

La operación es definitiva y transaccional: si ocurre un fallo se revierte todo el borrado. Solo se permite eliminar la última carga; si otra persona importa un archivo mientras está abierta la confirmación, la petición anterior se rechaza y debe revisarse la carga nueva.

Si se cargó dos veces el mismo archivo, la segunda carga puede tener cero consultas nuevas porque el sistema omitió duplicados. Eliminar esa segunda carga no borra los registros de la primera. Para retirarlos también, volver a eliminar la carga que quede como última.

Los indicadores y reportes se recalculan a partir de la información restante, y es posible volver a importar el archivo después del borrado. El archivo Excel o CSV original del equipo no se elimina.

## Archivo de prueba de 50 pacientes de Los Ríos

El archivo `outputs/los_rios_50/plantilla_pacientes_Los_Rios_50.xlsx` usa las 14 columnas y la hoja Pacientes de la plantilla Valdivia. Contiene 50 RUT distintos: 20 personas de la referencia con una nueva atención y 30 personas nuevas. Todos los domicilios son ficticios y se ubican en Valdivia, Región de Los Ríos.

Para probar con una base sin registros manuales:

1. Importar la plantilla original de 80 pacientes.
2. Importar el archivo nuevo de 50: se agregan 50 consultas y 30 pacientes nuevos, para un total de 110 pacientes únicos.
3. Eliminar la última importación: se borran esas 50 consultas y los 30 pacientes exclusivos. Los 20 pacientes compartidos recuperan sus datos previos y el total vuelve a 80.
4. Volver a cargar el archivo de 50 para comprobar que sus registros pueden procesarse nuevamente.

Si el objetivo es reemplazar una carga inicial, eliminarla antes de subir el nuevo archivo. Los nombres, mediciones, fechas y categorías declaradas son datos de demostración; las categorías se conservan como entradas ficticias y no se convierten en reglas normativas automáticamente.
