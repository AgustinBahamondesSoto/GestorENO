# Plantilla de demostración

La copia Excel de demostración está en `outputs/plantilla_demo/plantilla_pacientes_ficticios.xlsx`. Conserva las 14 columnas y los 80 registros del CSV proporcionado por el usuario, con tres filas de título antes del encabezado. El original no se modificó.

## Ajustes en la copia

- Normalización visual de los 80 RUT quitando puntos. Los dígitos verificadores originales ya eran correctos.
- Ajuste de tres edades para concordar con los intervalos escritos en el nombre de las condiciones de la propia planilla.
- Ajuste de tres combinaciones de nombre y sexo para los ejemplos de condiciones cervicouterinas o de próstata.
- Sustitución del tipo de consulta por control pediátrico o control de seguimiento, según la edad del ejemplo.
- Ajuste de doce pesos pediátricos como valores de simulación. No constituyen rangos de referencia clínica.
- Alineación de la fecha de los últimos exámenes con la fecha de consulta en 78 registros.
- Sustitución de los antecedentes por texto explícito de demostración, eliminando afirmaciones ficticias sobre trámites ya realizados ante SEREMI o registros oficiales.

Se conservaron las enfermedades y las categorías declaradas GES/AUGE, ENO, ambas o No aplica del archivo de referencia. No se verificó su correspondencia normativa: son entradas de prueba y no se cargan como reglas clínicas autorizadas. Las mediciones de signos vitales originales se conservaron; su plausibilidad clínica no se considera validada.

El detalle por fila y columna de los cambios está en `docs/plantilla_demo_cambios.json`. Los datos permiten comprobar el flujo del software; no permiten medir exactitud clínica.

## Importación

La aplicación admite tanto el CSV original como esta copia Excel. Ambos se probaron con 80 filas procesadas y cero filas inválidas, dentro de una transacción revertida para no incorporar datos de demostración a la base del usuario.

La cabecera se busca entre las primeras 20 filas. El CSV admite UTF-8 y Windows-1252, separado por coma o punto y coma. Las filas vacías y la fila de resumen `Total pacientes registrados:` no crean pacientes ni errores.

`Últimas consultas` se conserva como texto y, cuando empieza con DD-MM-AAAA, su fecha se usa como fecha de consulta. Una columna explícita `Fecha consulta` en AAAA-MM-DD tiene preferencia. `Condición del Problema` se conserva como condición declarada, separada del resultado del motor. La columna de enfermedades también alimenta el reconocimiento de texto.

Para una demostración limpia, importar una de las dos versiones. Como la copia cambia campos clínicos, importarla después del original agrega esas filas como consultas distintas del mismo paciente, según la regla de preservación del historial.
