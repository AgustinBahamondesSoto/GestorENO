# Manual de usuario de Gestor ENO

Este manual explica cómo ingresar, importar planillas, gestionar pacientes y atenciones, configurar reglas y descargar reportes. Los pasos corresponden a la versión del proyecto principal actualizada el 22 de noviembre de 2026. Las tareas habituales se realizan desde la web.

## 1 Acceder al sistema

1. Abre la dirección que te indique el equipo. En el computador donde está funcionando la aplicación local, la dirección es http://127.0.0.1:8000/. Esa dirección no permite acceder desde otro computador.
2. Escribe tu nombre de usuario y contraseña. Si todavía no tienes una cuenta, solicítala al administrador.
3. En el primer acceso, sigue el asistente para vincular una aplicación autenticadora de tu teléfono. Escanea el código QR e introduce el código temporal para terminar la configuración.
4. En los accesos siguientes, introduce tu contraseña y el código vigente de la aplicación autenticadora. Al completar la verificación podrás entrar a Indicadores.

No compartas contraseñas, el QR de configuración ni códigos de recuperación. Si el código temporal vence mientras lo escribes, utiliza el siguiente. Al terminar, pulsa Salir en el menú.

## Dónde realizar cada tarea

| Opción del menú | Para qué se utiliza | Página |
| --- | --- | --- |
| Importar planilla | Preparar, cargar, revisar y retirar archivos | 2 y 3 |
| Pacientes | Buscar, registrar y corregir datos personales | 4 |
| Ficha del paciente | Agregar y corregir enfermedades o atenciones | 5 |
| Enfermedades | Consultar el catálogo y configurar reglas | 6 |
| Indicadores | Filtrar población y descargar reportes | 7 |
| Ayuda y seguridad | Resolver problemas y recuperar el acceso | 8 |

En una pantalla pequeña, abre el botón de navegación para ver el menú. Administración solo aparece para cuentas autorizadas; no se necesita para cargar datos, crear reglas o registrar pacientes.

# 2 Preparar la planilla

Entra a Importar planilla y pulsa Descargar plantilla vacía. Completa una copia y conserva el archivo original. Utiliza las 14 columnas del formato del hospital y registra el domicilio y la comuna correspondientes a la persona, en la Región de Los Ríos.

| Columna de la plantilla | Contenido |
| --- | --- |
| Nombre / Apellido | Nombres y apellidos de la persona en sus columnas respectivas. |
| RUT | Identificador con dígito verificador. Puede llevar puntos y guion. |
| Edad | Edad en años enteros, entre 0 y 130. |
| Enfermedades crónicas / Complicaciones (listado) | Una o más enfermedades; sepáralas con punto y coma o salto de línea. |
| Previsión | Por ejemplo, Fonasa A, Fonasa B, Isapre o Particular. |
| Peso (kg) | Valor positivo, con hasta dos decimales. |
| Sexo | Por ejemplo, F, M u Otro. |
| Domicilio y comuna | Dirección y comuna. No se restringe automáticamente a Los Ríos. |
| Últimas consultas | Descripción de la atención. Si agregas una fecha al inicio, usa DD-MM-AAAA. |
| Antecedentes médicos | Antecedentes disponibles, escritos de forma clara. |
| Signos vitales (últimos exámenes) | Mediciones disponibles con sus unidades. |
| Destino del paciente | Destino o derivación correspondiente. |
| Condición del Problema (GES/AUGE - ENO) | Condición declarada en la planilla; la clasificación del sistema depende de sus reglas. |

## Revisar antes de cargar

Usa Excel .xlsx o CSV .csv, con un máximo de 10 MB y 50.000 filas. Conserva los encabezados; la plantilla descargada ya tiene la hoja Pacientes. El formato anterior de ocho columnas también se admite.

Nombre, RUT, Edad, Peso, Sexo y Previsión deben tener un valor en cada fila. También deben existir las columnas Antecedentes médicos y Signos vitales, aunque sus celdas pueden estar vacías. No escribas valores inventados para completar información desconocida.

Ejemplo de Últimas consultas: 29-07-2026 - Control de seguimiento. Si utilizas una columna adicional Fecha consulta, admite una fecha de Excel o texto AAAA-MM-DD.

Durante demostraciones y pruebas usa datos ficticios. No se asigna una categoría clínica por el solo hecho de escribir ENO o GES/AUGE en la planilla.

# 3 Importar y retirar una carga

## Cargar el archivo

1. Entra a Importar planilla y selecciona el archivo en Planilla Excel o CSV.
2. Pulsa Importar registros y espera el resumen de la carga.
3. Revisa las filas leídas, las consultas nuevas, los pacientes nuevos, las inválidas y las ya importadas.
4. Abre el detalle de la importación desde el nombre del archivo para consultar las inconsistencias. Corrige las filas indicadas en una copia de la planilla y vuelve a cargarla cuando corresponda.

| Resultado | Cómo interpretarlo |
| --- | --- |
| Pacientes nuevos | Personas que todavía no existían con ese RUT. |
| Consultas nuevas | Atenciones incorporadas; un paciente puede tener varias. |
| Inválidas o errores | Filas que no se incorporaron por un problema de validación. |
| Ya importadas u omitidas | Filas reconocidas como cargadas anteriormente; no se duplican. |

Una carga puede incorporar las filas válidas aunque otras tengan errores. Si falta una columna obligatoria o el archivo no se puede leer, se rechaza la estructura. Corrige lo indicado en el mensaje antes de reintentar.

## Eliminar la última importación

1. Entra a Importar planilla y pulsa Eliminar última importación.
2. Comprueba el nombre del archivo y las cantidades de consultas y pacientes que se eliminarán o conservarán.
3. Si es la carga que necesitas retirar, marca la confirmación y pulsa Eliminar importación y sus datos. Si no corresponde, cancela.
4. Revisa los pacientes e indicadores restantes. Después puedes cargar el archivo corregido.

El borrado es definitivo desde la web. Elimina las consultas de ese lote y los pacientes exclusivos que corresponda retirar. Conserva las atenciones de otros lotes, los registros manuales y el catálogo y las reglas. El Excel original de tu computador no se borra.

Solo se elimina la carga más reciente. Si cargaste dos veces el mismo archivo y la segunda carga incorporó cero consultas, borrar esa segunda carga no retira los datos de la primera. Revisa nuevamente cuál quedó como última antes de decidir otro borrado.

El sistema intenta recuperar los datos anteriores de las fichas afectadas y conserva las correcciones posteriores que puede identificar. Revisa la ficha y el resumen de la operación; eliminar una carga no equivale a vaciar toda la base.

# 4 Buscar y registrar pacientes

## Buscar y abrir el historial

1. Entra a Pacientes.
2. Escribe un nombre o RUT en Buscar por nombre o RUT y pulsa Buscar.
3. Abre el RUT de la persona para consultar su ficha. Comprueba su identidad antes de modificar cualquier dato.
4. Si no encuentras el resultado, revisa el texto de búsqueda, límpialo y vuelve a buscar. Revisa también las otras páginas del listado.

## Registrar una persona nueva

1. Antes de crearla, busca su RUT para comprobar si ya existe.
2. Pulsa Registrar paciente.
3. Completa RUT, Nombres, Edad, Sexo y Previsión. Añade Apellidos y Domicilio y comuna cuando dispongas de ellos.
4. Guarda el formulario y comprueba los datos de la ficha creada.

El RUT se normaliza y se valida por su dígito verificador. Los formatos con y sin puntos corresponden a la misma identidad. Si ese RUT ya existe, abre su ficha para agregar una atención en lugar de crear otra persona.

## Corregir datos personales

1. Abre la ficha del paciente y pulsa Editar paciente.
2. Corrige los datos necesarios y guarda.
3. Comprueba el nombre, RUT, edad, sexo, previsión y domicilio que aparecen en la ficha.

Editar paciente modifica los datos actuales de la persona. Las atenciones anteriores conservan los datos demográficos que tenían registrados. Para corregir antecedentes o signos vitales de una atención, usa Corregir datos de esta atención, explicado en la página siguiente.

Una corrección de RUT no fusiona automáticamente dos fichas. Si existen dos personas registradas que deberían ser una sola, solicita revisión al administrador. Las futuras planillas deben usar el RUT correcto.

## Qué muestra la ficha

La ficha reúne los datos personales y las consultas, con fecha, clasificación, enfermedades, antecedentes, signos vitales y origen del registro. El enlace a la importación permite localizar el lote y la fila de una atención cargada desde Excel o CSV.

El Registro de cambios de la ficha muestra los últimos eventos manuales con fecha y usuario. Los pacientes sin consultas pueden existir en el sistema; registrar una ficha no equivale a registrar una enfermedad.

# 5 Agregar y corregir atenciones

## Añadir una enfermedad o una atención

1. Busca al paciente, abre su ficha y pulsa Agregar enfermedad o atención.
2. Indica la Fecha de atención.
3. Selecciona las Enfermedades del catálogo. En un computador Windows puedes mantener Ctrl para seleccionar varias.
4. Si falta una enfermedad, escríbela en Otra enfermedad; se incorporará al catálogo al guardar.
5. Completa los antecedentes, signos vitales, peso y destino disponibles. El peso es opcional en el registro manual.
6. Pulsa Guardar y clasificar. Comprueba el mensaje y la nueva consulta del historial.

Debes seleccionar una enfermedad, escribir una nueva o registrar antecedentes médicos. Agregar una atención conserva las anteriores y no crea otro paciente.

## Corregir una atención existente

1. En la ficha, identifica la atención por su fecha y contenido.
2. Pulsa Corregir datos de esta atención.
3. Modifica los datos y pulsa Guardar y clasificar.
4. Reabre la consulta y verifica que el cambio y la clasificación sean los esperados.

Al corregir una consulta importada se mantiene su referencia al lote original. Volver a importar el mismo archivo no sobrescribe automáticamente esa corrección. Si se trata de una atención diferente, usa Agregar enfermedad o atención.

## Entender el resultado

| Texto mostrado | Qué significa |
| --- | --- |
| ENO o GES/AUGE | Una regla activa asignó esa categoría a la atención. |
| Sin coincidencias | Las reglas activas no reconocieron una coincidencia. No certifica ausencia de enfermedad. |
| Sin atenciones | La persona tiene ficha, pero todavía no tiene consultas registradas. |

Una enfermedad puede existir en el catálogo sin tener una regla. Si se registró correctamente pero no se clasifica, revisa Enfermedades y reglas con la persona responsable del diccionario. Una persona puede tener categorías diferentes en distintas consultas.

El cifrado de los campos clínicos es automático. En los formularios se escriben y leen normalmente; no es necesario cifrar el texto a mano.

# 6 Enfermedades y reglas de clasificación

Entra a Enfermedades para buscar términos y revisar sus reglas. El catálogo reúne los términos conocidos por esta instalación; no constituye una lista normativa completa de enfermedades.

## Agregar una enfermedad al catálogo

1. Pulsa Agregar enfermedad, escribe su nombre y guarda.
2. Si ya existe, búscala y utiliza el término registrado.
3. Después de guardarla se abre la creación de su regla. Puedes completarla o cancelarla y hacerlo más adelante.

Agregar una enfermedad al catálogo no la asigna por sí solo a un paciente. Para hacerlo, registra o corrige una atención desde su ficha.

## Crear una regla

1. Pulsa Crear regla en Enfermedades, o Crear regla de clasificación en Indicadores.
2. Escribe un Nombre de la regla que permita reconocer su propósito y selecciona la Enfermedad.
3. Selecciona la Clasificación ENO o GES/AUGE acordada con la persona responsable del diccionario.
4. En Tipo, utiliza Palabra clave para una coincidencia de texto. En Patrón, escribe el término que debe reconocer. Las expresiones regulares requieren revisión técnica.
5. Define la Prioridad y deja Activa marcada si debe aplicarse. Un número menor se evalúa primero.
6. Guarda y espera la confirmación de reclasificación. Después revisa algunos pacientes y el resultado filtrado en Indicadores.

Al guardar una regla se reclasifica el historial completo automáticamente. No es necesario usar Django Admin ni ejecutar comandos. La cantidad de consultas procesadas no es una cantidad de pacientes nuevos.

## Modificar o desactivar una regla

Selecciona el nombre de la regla en Enfermedades. Corrige el patrón, la categoría o la prioridad, o desmarca Activa, y guarda. El sistema vuelve a calcular las clasificaciones. Actualizar clasificaciones permite repetir el cálculo desde la web.

La primera regla coincidente determina la categoría principal; las otras coincidencias aportan enfermedades detectadas. Si dos reglas tienen la misma prioridad, se utiliza su orden de identificación. Revisa los resultados cuando haya reglas superpuestas.

El reconocimiento por palabras no interpreta por sí solo negaciones, antecedentes familiares o todo el contexto clínico. Las categorías y reglas deben validarse con el establecimiento antes de interpretar los resultados como clasificación clínica.

# 7 Filtrar indicadores y descargar Excel

## Seleccionar la población

1. Entra a Indicadores.
2. Completa Edad desde y Edad hasta si necesitas un intervalo. Selecciona Sexo, Previsión, Categoría o Enfermedad según la consulta.
3. Pulsa Aplicar filtros.
4. Revisa Pacientes únicos y la tabla con RUT, nombre, enfermedades y clasificación. Abre el RUT para consultar un historial.
5. Pulsa Limpiar para volver a consultar la población sin esos filtros.

Ejemplo de consulta: selecciona una enfermedad que exista en el catálogo y una categoría que tenga configurada. Al combinar Enfermedad y Categoría, una misma atención debe cumplir ambas condiciones. Si no hay resultados, prueba cada filtro por separado y revisa las reglas activas.

## Interpretar los conteos

Los indicadores cuentan personas únicas por RUT. Un paciente con varias consultas no aumenta por ello el total de personas. Los filtros de edad, sexo y previsión usan la ficha actual; los filtros clínicos seleccionan las atenciones correspondientes.

Los porcentajes se calculan sobre la población filtrada. Una persona puede aparecer en varias enfermedades o categorías; sumar grupos superpuestos no necesariamente da el total de pacientes.

## Exportar el resultado

1. Comprueba que los filtros y la población mostrados sean los que necesitas.
2. Pulsa Descargar Excel y abre el archivo descargado.
3. Contrasta Resumen y Pacientes filtrados con la web. La descarga incluye todas las páginas del resultado, no solo la visible.

| Hojas del archivo | Contenido |
| --- | --- |
| Resumen y Pacientes filtrados | Total de personas y listado con RUT, nombre, enfermedades y clasificación. |
| Edad, Sexo y Previsión | Distribución demográfica de los resultados. |
| GES y ENO y Prevalencia | Distribución por categoría y enfermedad. |
| ENO pendientes y GES vigentes | Personas y número de consultas que cumplen esos estados y los filtros. |

ENO pendientes y GES vigentes son reportes internos. El sistema no envía notificaciones automáticamente a organismos externos. Los estados se actualizan desde Administración por personal autorizado.

El Excel descargado contiene información legible. Guárdalo y compártelo solo con las personas autorizadas. No se utiliza como reemplazo de la plantilla de importación.

# 8 Resolver problemas y cuidar el acceso

| Situación | Qué hacer |
| --- | --- |
| La página local no abre | Comprueba que el sistema esté iniciado en ese computador. Solicita ayuda al equipo si no lo está. |
| Usuario o contraseña rechazados | Comprueba la escritura y las mayúsculas. Si no puedes acceder, contacta al administrador. |
| El código del autenticador no funciona | Usa un código vigente de Gestor ENO y revisa la fecha y hora automáticas del teléfono. No reutilices un código ya aceptado. |
| Se perdió el teléfono | Utiliza un código de recuperación previamente guardado si está disponible. Si no lo tienes, solicita recuperación al administrador. |
| Faltan columnas o el archivo no se lee | Descarga la plantilla vacía, conserva sus encabezados y comprueba que el archivo sea .xlsx o .csv. |
| Una fila no se incorpora | Abre el detalle de la carga y revisa RUT, campos obligatorios, edad, peso y fecha. Corrige lo indicado antes de reimportar. |
| No aparecen pacientes en el filtro | Pulsa Limpiar y revisa cada filtro por separado. Comprueba que existan atenciones y reglas que correspondan. |
| La enfermedad figura Sin coincidencias | Comprueba que exista una regla activa cuyo patrón reconozca el texto. Acuerda cualquier cambio con la persona responsable. |
| Al volver a cargar no aparecen consultas nuevas | Revisa Ya importadas u Omitidas. El archivo puede haber sido procesado anteriormente. |

## Preparar la recuperación del acceso

Después de iniciar sesión con ambos factores, abre la dirección del sistema y añade /account/two_factor/. Allí puedes consultar la configuración de autenticación y acceder a los códigos de recuperación. Guárdalos en un lugar protegido; cada código es de un solo uso. No los incluyas en capturas ni en este manual.

El proyecto principal y la copia de testing tienen cuentas, datos y configuración independientes. Utiliza el autenticador vinculado a la instalación a la que estás entrando. Si cambias de teléfono, acuerda la transición antes de perder el acceso al anterior.

## Solicitar ayuda con información útil

Indica la pantalla, la acción que intentaste, el mensaje exacto y el nombre del archivo si corresponde. Oculta datos de pacientes en las capturas cuando no sean necesarios. No envíes contraseñas, códigos ni claves de cifrado.

Usa Salir al terminar, especialmente en equipos compartidos. Si sospechas un acceso ajeno o una eliminación accidental, deja de modificar datos y avisa al administrador para que revise lo ocurrido.
