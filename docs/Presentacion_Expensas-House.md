# Presentación académica de Expensa House

**Materia:** Técnicas de Procesamiento Digital de Imágenes

**Año y cuatrimestre de cursada:** 2026 · Segundo cuatrimestre

**Nombre y apellido:** Griselda Blanco

**Docente:** Juan Ignacio Bonini

**Repositorio:** https://github.com/griseldablanco78-blip/Expensas_House
**Web:** https://expensas-house-griselda-blanco.vercel.app
**Usuario de prueba:** `test123`
**Contraseña de prueba:** `PruebasTest1234`

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
