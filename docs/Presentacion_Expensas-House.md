# Presentación académica de Expensa House

**Materia:** Técnicas de Procesamiento Digital de Imágenes

**Año y cuatrimestre de cursada:** 2026 · Segundo cuatrimestre

**Nombre y apellido:** Griselda Blanco

**Docente:** Juan Ignacio Bonini

**Repositorio:** https://github.com/griseldablanco78-blip/Expensas_House
**Web:** https://expensas-house-griselda-blanco.vercel.app

## Resumen

Desarrollé Expensa House para administrar despensa, compras, presupuesto y comprobantes desde Android y desde una web. Ambos clientes consultan una API Python compartida.

## Motivación del proyecto

Expensa House surgió para reunir información del hogar que suele quedar distribuida entre anotaciones, tickets impresos y mensajes: qué productos hay, cuáles faltan, cuánto se gastó y dónde conviene consultar una oferta. La posibilidad de registrar una compra desde el celular y revisarla desde la web busca facilitar la organización cotidiana y el seguimiento del presupuesto. Conservar la fecha y los precios de cada compra permite consultar cuánto costaba un producto en un momento anterior.

## Problemáticas encontradas y soluciones aplicadas

| Problemática | Solución aplicada y alcance |
| --- | --- |
| El teléfono y la web dependían de una dirección local o de un túnel que dejaba de responder. | Se configuró una dirección HTTPS fija con web y API en Vercel, persistencia PostgreSQL e imágenes privadas en Supabase. El servicio depende de la disponibilidad y límites de los planes gratuitos. |
| Los datos de la app y la web podían no coincidir al cambiar de almacenamiento o cuenta. | Se revisó la sincronización, se respaldaron los datos y se conservó la información cargada en el hogar compartido. La separación de hogares independientes sigue como mejora futura. |
| El OCR reconocía texto, pero podía mezclar encabezados fiscales con productos o perder nombres partidos entre líneas. | Se separó el reconocimiento de la interpretación, se excluyeron datos fiscales y medios de pago del listado de productos, y se conservaron nombres distribuidos en varias líneas, incluso con espacios vacíos entre nombre y precio. La revisión de importes sigue siendo necesaria. |
| La calidad de lectura variaba entre Android y la web. | Android utiliza ML Kit; la web utiliza Tesseract.js con español, ampliación de texto pequeño, contraste, margen y procesamiento opcional de sombras. No se afirma una precisión equivalente ni un porcentaje sin evaluar tickets reales. |
| Descuentos e IVA podían interpretarse de forma incompleta o sumarse incorrectamente. | Se registran precio unitario, descuento e importe neto; el IVA se conserva por separado. El presupuesto descuenta el total pagado y no suma de nuevo el IVA incluido. Los descuentos generales ambiguos requieren revisión. |
| Reintentar un envío por una falla de conexión podía duplicar un gasto. | Cada ticket tiene un identificador estable y el backend comprueba si ya fue registrado antes de modificar el presupuesto. |
| «Cargar ticket» en Android conducía a un gasto manual y no al flujo de fotografía. | Se diferenciaron las acciones de cargar foto o galería y registrar un gasto manual. Las pruebas instrumentadas comprueban la acción asociada al botón. |
| Android no mostraba el resumen y el detalle de ofertas disponibles en la web. | Se incorporaron los campos de comparación de la API, detalles desplegables y acceso a resultados posteriores a los diez iniciales. La vigencia se confirma en el supermercado. |
| Era difícil consultar precios de compras anteriores. | Se conservan productos e importes con fecha de compra y se ofrece consulta de resúmenes por fecha. Un gasto antiguo sin productos guardados no se reconstruye automáticamente. |
| No había evidencia suficiente para declarar exactitud predictiva. | Se distinguieron las reglas de la aplicación, los modelos OCR preentrenados y el experimento Random Forest. Las métricas no reproducibles se identifican como pendientes; no se inventan porcentajes. |

Las pruebas se ejecutan con datos ficticios y almacenamiento temporal para verificar tickets, presupuesto, reintentos, ofertas y resúmenes sin modificar las compras personales.

## Eje de procesamiento digital de imágenes: del ticket al presupuesto

**La fotografía del ticket se transforma en un registro de compra revisable que conserva los productos, sus precios y la fecha, y actualiza el presupuesto al confirmar el gasto.**

1. **Adquisición de imagen:** se toma una foto o se elige desde la galería. Se conserva el comprobante completo en color, sin recortar sus bordes.
2. **Preparación para lectura:** la web utiliza una copia de la imagen original con resolución acotada, ampliación de letras pequeñas, escala de grises, contraste y margen blanco. Puede aplicar umbral adaptativo para sombras. Esta copia se procesa por separado de la fotografía archivada.
3. **Reconocimiento óptico de caracteres:** Tesseract.js con modelo LSTM español en la web, y ML Kit en Android, convierten la imagen en texto. En la web se comparan dos distribuciones de lectura para reducir errores al separar nombres y precios. No se entrenó un modelo propio ni se garantiza exactitud sobre cualquier fotografía.
4. **Interpretación y revisión:** el backend separa descripción, cantidad, precio unitario, descuento e importe neto. Una presentación como «2.25L» pertenece al nombre del producto y no es un precio. Los datos fiscales y los fragmentos sin nombre legible no se cargan como productos. El usuario revisa y corrige lo reconocido antes de confirmar.
5. **Registro del comprobante:** al confirmar se guardan fecha, supermercado, productos, precios, descuentos, IVA cuando está informado, total pagado, texto y referencia a la fotografía privada.
6. **Actualización del presupuesto:** se registra un gasto por el **total efectivamente pagado del ticket**. El disponible se calcula como **presupuesto mensual − gastos registrados del mes**. El IVA incluido no se suma de nuevo y reenviar el mismo ticket no duplica el gasto. Una lectura o una foto sin confirmar no modifica el presupuesto.
7. **Consulta posterior:** los resúmenes por fecha permiten recordar qué se compró, dónde y a qué precio, conservando los importes históricos de cada compra.

Este recorrido conecta adquisición y mejora de imágenes, OCR, validación de datos y una aplicación concreta de gestión del hogar. Las pruebas con fotos sintéticas verifican nombres completos, presentaciones decimales y precios; medir la exactitud en tickets reales requiere una muestra específica.

## Imágenes reales de productos en las ofertas

**El buscador muestra la fotografía del producto proporcionada por la fuente externa, junto con su nombre, supermercado, precio y condiciones.** El backend consulta catálogos públicos de Día, Coto, Carrefour, Vea y Jumbo mediante sus endpoints de catálogo, extrae la fotografía de la variante (`imageUrl` en VTEX; `image_url` en Coto) y devuelve `image_url` a los clientes. La web y Android utilizan esa dirección para mostrar la imagen real del catálogo. No se generan fotografías mediante IA ni se inventan precios. Las ofertas manuales pueden incorporar una foto suministrada por el usuario.

Las imágenes ayudan a reconocer marca y presentación, pero no sustituyen la comparación de tamaño, precio y condiciones. Si la API no aporta una foto o el recurso deja de estar disponible, la interfaz informa que no hay imagen. La consulta externa depende de la disponibilidad y permisos de la fuente. Ratoneando permanece como consulta enlazada y proveedor opcional, no como integración garantizada.

## Funcionalidades y responsabilidades de cada módulo

| Módulo | Qué puede hacer el usuario | Cómo funciona |
| --- | --- | --- |
| Acceso y sesión | Iniciar sesión y acceder según sus permisos. | La API verifica credenciales y permisos; los clientes mantienen la sesión. Actualmente la cuenta publicada corresponde a un hogar compartido. |
| Inicio y navegación | Consultar el estado general y abrir cada sección. | Reúne accesos a stock, compras, ofertas y presupuesto. |
| Despensa o stock | Registrar productos, cantidades cerradas y en uso; actualizar faltantes. | Android conserva una copia Room y sincroniza los cambios con la API compartida. |
| Lista de compras | Agregar productos pendientes y llevarlos desde una oferta a la lista. | Conserva la información del producto y su estado; no registra automáticamente un gasto al buscar. |
| Ofertas e imágenes externas | Buscar por nombre, comparar precios y abrir el detalle o la página del supermercado. | Normaliza palabras y presentaciones, combina ofertas guardadas y catálogos habilitados, y muestra su imagen, fuente y condiciones cuando existen. |
| Imagen del ticket y OCR | Fotografiar o elegir un comprobante, leerlo y revisar los productos reconocidos. | Separa la imagen archivada de la copia de lectura; Tesseract.js o ML Kit extraen texto y Python lo transforma en líneas revisables. |
| Registro contable | Confirmar supermercado, fecha, precios, descuentos, IVA y total pagado. | Valida los cálculos y registra el comprobante una sola vez. La fotografía sin confirmar no descuenta dinero. |
| Presupuesto | Consultar presupuesto, gasto registrado y saldo disponible. | El total confirmado del ticket se suma a los gastos del mes y se resta del presupuesto disponible. |
| Resúmenes y precios históricos | Elegir una fecha y recordar productos, supermercado y precios de esa compra. | Consulta los importes guardados en esa fecha sin reemplazarlos por precios actuales. Permite descargar texto y consultar la foto del comprobante desde la web. |
| Boti House | Consultar ofertas, faltantes y presupuesto mediante mensajes. | Usa reglas y palabras clave sobre la información disponible; no es un modelo generativo entrenado por el proyecto. |
| Voz a texto | Dictar búsquedas o consultas. | El servicio de reconocimiento del dispositivo convierte el audio en texto y lo entrega al módulo correspondiente. |
| Sincronización y persistencia | Consultar los mismos datos desde Android y la web cuando hay conexión. | FastAPI comparte las reglas; PostgreSQL conserva los registros, Storage privado guarda fotos y Room mantiene la copia local Android. |

## Ejemplo de interpretación de un ticket

El formato de supermercado revisado imprime `2,00 X 2749,00` encima de `CUNNING COLA 2,25L (21,00) 5498,00`. La interpretación correcta conserva el nombre y la presentación, asigna dos unidades a $2.749 y registra $5.498 como total pagado. `(21,00)` es una alícuota, no el precio unitario. El IVA contenido de $954,20 ya forma parte del total y no se agrega nuevamente. El importe entregado en efectivo y el vuelto no se convierten en gastos ni productos.

## Material incluido en el ZIP

El ZIP para el aula contiene únicamente el código y `ENLACES_PROYECTO.txt` con GitHub y Vercel. Esta presentación, el informe breve y los cuadernillos quedan disponibles en GitHub. La APK Android 1.3.2 se ofrece por separado en [GitHub Releases](https://github.com/griseldablanco78-blip/Expensas_House/releases/tag/v1.3.2). La foto de ejemplo tampoco se incluye en la entrega.

## Tecnologías

El proyecto utiliza Kotlin y Jetpack Compose en Android; Room/SQLite para la copia local; Retrofit para llamadas HTTP; FastAPI y Python en Vercel; HTML, CSS y JavaScript en la web; PostgreSQL y Storage privado de Supabase para persistencia; Tesseract.js y modelos LSTM español para OCR en el navegador; y scikit-learn para un experimento predictivo. El desarrollo local conserva adaptadores JSON y SQLite.

## Tres módulos principales de asistencia

1. **Voz a texto:** convierto el habla en texto mediante Web Speech API o el reconocedor Android. Luego utilizo el texto para buscar ofertas o completar consultas.
2. **Chatbot Boti House:** responde mediante reglas a consultas de ofertas, presupuesto y faltantes. No entrené un modelo generativo.
3. **Buscador de ofertas:** normaliza la consulta, busca coincidencias y compara precios publicados. Las ofertas pueden ser manuales o provenir de fuentes externas configuradas.

También utilizo OCR para leer tickets. El motor reconoce texto, mientras que las reglas de Python separan productos, cantidades y precios.

## Predicción

El repositorio contiene un experimento con Random Forest para clasificar si un producto necesita reposición. El script utiliza categoría, frecuencia de consumo y gasto acumulado; el dataset limpio requerido no está incluido, por lo que no se informa una exactitud reproducible. El objetivo fue predecir stock crítico.

Todavía no incorporé ese modelo a la operación principal. Android identifica faltantes con una regla simple basada en el stock disponible.

## Datos móviles y web

Android guarda una copia en Room. Al iniciar o modificar datos, intenta sincronizar una instantánea con FastAPI. La web desplegada obtiene el estado central desde la API y actualiza sus módulos cada quince segundos.

La web y la API están alojadas en Vercel y guardan datos en Supabase. No dependen de una computadora encendida ni de un túnel. La sincronización requiere conexión. El plan gratuito de Supabase puede pausar el proyecto por baja actividad y permite reactivarlo desde el panel.

## Enlaces de documentación

- [Repositorio GitHub](https://github.com/griseldablanco78-blip/Expensas_House)
- [Cuadernillo técnico](../CUADERNILLO_TECNICO_IA.md)
- [Arquitectura](ARQUITECTURA.md)
- [Escáner y ofertas](ESCANER_Y_OFERTAS.md)
- [Guía de publicación](../deploy/VERCEL.md)

## Alcance y próximos pasos

La versión actual es un proyecto académico con datos cargados por usuarios y almacenamiento persistente en la nube. Las cuentas y sesiones tienen tablas propias; el estado del hogar usa temporalmente una fila JSONB. La cuenta publicada es compartida. Quedan pendientes la normalización de compras/productos en tablas independientes, la separación de hogares y un histórico suficiente para validar modelos predictivos. Ver [despliegue y límites](DESPLIEGUE_NUBE.md).

Actualización de ofertas: Día, Carrefour, Vea y Jumbo utilizan sus catálogos públicos VTEX; Coto se consulta mediante la búsqueda pública usada por su tienda. En Coto se compara el precio de una unidad en la sucursal 200, sin aplicar descuentos que exigen varias unidades o un medio de pago. Las fotografías provienen del catálogo correspondiente. La recomendación top es el menor precio entre presentaciones comparables, con advertencia cuando falta confirmar el tamaño. Android muestra dos tarjetas por fila y reserva las condiciones y la fuente para el detalle ampliable.
