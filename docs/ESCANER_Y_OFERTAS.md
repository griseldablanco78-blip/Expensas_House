# Escáner de tickets, productos y fotografías de ofertas

Actualización: 26 de noviembre de 2026.

## Despliegue actual

Web y API FastAPI funcionan bajo la URL fija de Vercel. PostgreSQL conserva datos y cuentas; Supabase Storage guarda fotografías privadas. No se requiere PC encendida ni túnel. Los límites y pausas del plan gratuito siguen aplicándose.

## Recorrido de la fotografía del ticket

1. Se elige una foto JPG, PNG o WebP (hasta 10 MB y 25 megapíxeles). La aplicación conserva el comprobante completo como JPEG de respaldo.
2. La web crea una copia para lectura desde la imagen original, con resolución acotada, ampliación de texto pequeño, grises, contraste y margen. El modo adaptativo de sombras se ejecuta en el navegador. Android utiliza ML Kit Text Recognition v2 con modelo latino incluido.
3. Tesseract.js con modelo LSTM español reconoce texto en la web. Se comparan dos distribuciones de lectura y se priorizan renglones de productos sobre pies fiscales. Puede releerse una zona del encabezado para proponer el supermercado. No se cobra una API de visión ni se entrenó un modelo propio.
4. Texto e imagen preparada se envían a `/api/receipts/draft`. El backend interpreta cantidades, nombres e importes. Se conservan descripciones partidas y cantidades/precios impresos en el renglón anterior al nombre. En tickets que informan ambos valores, `TOTAL PRODUCTOS` se trata como subtotal de artículos y se prioriza el importe del renglón final `TOTAL`; los descuentos globales no se confunden con nombres de productos.
5. Supermercado y fecha se proponen cuando se reconocen en el encabezado. Son editables. `2,25L` es una presentación y `(21,00)` una alícuota; ninguna debe convertirse en precio.
6. El usuario revisa descripción, cantidad, precio unitario, descuento, neto, IVA y total. La pantalla distingue la suma de productos reconocidos, el subtotal impreso cuando se detecta, la diferencia de ajustes y el importe pagado. Se debe cotejar el campo de total pagado con el último renglón `TOTAL` de la foto. Si el ticket declara descuento cero y sus netos coinciden con el total, un precio unitario dudoso puede calcularse desde neto/cantidad con advertencia. No se completa una marca ilegible con nombres inventados.
7. `/api/receipts/confirm` valida y registra el gasto una sola vez. El total pagado se descuenta del presupuesto disponible; el IVA incluido no se suma otra vez. La foto sin confirmar no modifica el presupuesto.
8. El resumen por fecha conserva productos y precios históricos; la web permite consultar la imagen y descargar el detalle en `.txt` con sesión autorizada.

El OCR local Python sigue como opción de desarrollo con Pillow, pytesseract/Tesseract y OpenCV opcional para sombras. No es el motor utilizado por el despliegue web en Vercel.

## Fotografías y precios de ofertas

`catalog_search.py` consulta catálogos públicos de Día, Coto, Carrefour, Vea y Jumbo y extrae precio, marca, disponibilidad, enlace y la fotografía de la variante (`imageUrl` en VTEX; `image_url` en Coto). La API entrega `image_url` y los clientes muestran esa fotografía real junto con su fuente. Si la imagen falta o deja de estar disponible, la interfaz lo informa. No se generan imágenes ni precios con IA. Ratoneando es un enlace de consulta y un proveedor opcional sujeto a autorización; no hay cobertura garantizada de todas las tiendas.

### Búsqueda a partir de una imagen

En la web, `visual-search.js` acepta imágenes que el navegador pueda decodificar, incluidos dibujos o ilustraciones sencillos. Primero Tesseract.js amplía hasta 3× las fotos pequeñas para extraer marca y palabras impresas; una familia leída del envase tiene prioridad sobre una categoría visual contradictoria. Si el envase no aporta texto útil, CLIP ViT-B/32 propone categorías generales. La consulta resultante busca en los catálogos de supermercados. El backend entrega pequeñas vistas de hasta cuatro fotos de productos por tienda; el navegador compara los embeddings CLIP de esas fotos con el de la imagen cargada y reordena las ofertas por similitud visual. Entre los resultados visualmente más cercanos, el menor precio se marca como top.

Esto no es un generador de descripciones abiertas ni reconoce todos los objetos posibles: la búsqueda visual local depende de que los catálogos devuelvan candidatos de la familia correcta, y CLIP puede confundir categorías parecidas si no hay texto legible. El resultado visual es una similitud entre embeddings, no una probabilidad de acierto ni un entrenamiento nuevo. La búsqueda sigue siendo editable y conviene revisar la foto, la presentación, las condiciones y el precio. Los archivos del modelo y las etiquetas están alojados en el proyecto de Vercel; la imagen no se envía a Hugging Face ni a otro proveedor externo de IA.

## Verificación y límites

Las pruebas locales usan almacenamiento temporal y fotos sintéticas. La foto real de DIA se prueba únicamente cuando se indica su ruta local mediante `E2E_RECEIPT_FIXTURE`; no se incorpora a Git ni se registra en el hogar publicado. Un carácter ambiguo como la letra L frente al número 1 puede requerir corrección manual. Las advertencias no se presentan como un porcentaje de exactitud ni como garantía sobre cualquier foto.

La cuenta publicada del hogar es compartida y contiene información cargada por usuarios; las pruebas que escriben compras se ejecutan en entornos locales ficticios. Ver [presentación](Presentacion_Expensas-House.md), [informe breve](INFORME_PRESENTACION.md) y [cuadernillo](../CUADERNILLO_TECNICO_IA.md).

Actualización de ofertas: Día, Carrefour, Vea y Jumbo utilizan sus catálogos públicos VTEX; Coto se consulta mediante la búsqueda pública usada por su tienda. En Coto se compara el precio de una unidad en la sucursal 200, sin aplicar descuentos que exigen varias unidades o un medio de pago. Las fotografías provienen del catálogo correspondiente. La recomendación top es el menor precio entre presentaciones comparables, excluyendo otros tamaños y presentaciones sin confirmar cuando la consulta especifica peso o volumen. Android muestra dos tarjetas por fila y reserva las condiciones y la fuente para el detalle ampliable.

Los avisos de beneficios personales se incorporan desde `loyalty_programs.py`, sin modificar el precio ni el ranking. Las fuentes oficiales de referencia son [Club Día](https://diaonline.supermercadosdia.com.ar/clubdia), [Comunidad Coto](https://www.comunidadcoto.com.ar/static/preguntas.html), [Mi Carrefour](https://www.micarrefour.com.ar/terminos-condiciones), [Vea Ahorro](https://www.vea.com.ar/faq-frecuentes) y [Jumbo Más](https://www.jumbomas.com.ar/preguntas-frecuentes-jumbo-mas). No se solicitan números de tarjeta ni credenciales de estos programas.
