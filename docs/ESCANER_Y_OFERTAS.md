# Escáner de tickets, productos y fotografías de ofertas

Actualización: 18 de noviembre de 2026.

## Despliegue actual

Web y API FastAPI funcionan bajo la URL fija de Vercel. PostgreSQL conserva datos y cuentas; Supabase Storage guarda fotografías privadas. No se requiere PC encendida ni túnel. Los límites y pausas del plan gratuito siguen aplicándose.

## Recorrido de la fotografía del ticket

1. Se elige una foto JPG, PNG o WebP (hasta 10 MB y 25 megapíxeles). La aplicación conserva el comprobante completo como JPEG de respaldo.
2. La web crea una copia para lectura desde la imagen original, con resolución acotada, ampliación de texto pequeño, grises, contraste y margen. El modo de sombras agrega umbral local. Android utiliza ML Kit Text Recognition v2 con modelo latino incluido.
3. Tesseract.js con modelo LSTM español reconoce texto en la web. Se comparan dos distribuciones de lectura y se priorizan renglones de productos sobre pies fiscales. Puede releerse una zona del encabezado para proponer el supermercado. No se cobra una API de visión ni se entrenó un modelo propio.
4. Texto e imagen preparada se envían a `/api/receipts/draft`. El backend interpreta cantidades, nombres e importes. Se conservan descripciones partidas y cantidades/precios impresos en el renglón anterior al nombre.
5. Supermercado y fecha se proponen cuando se reconocen en el encabezado. Son editables. `2,25L` es una presentación y `(21,00)` una alícuota; ninguna debe convertirse en precio.
6. El usuario revisa descripción, cantidad, precio unitario, descuento, neto, IVA y total. Si el ticket declara descuento cero y sus netos coinciden con el total, un precio unitario dudoso puede calcularse desde neto/cantidad con advertencia. No se completa una marca ilegible con nombres inventados.
7. `/api/receipts/confirm` valida y registra el gasto una sola vez. El total pagado se descuenta del presupuesto disponible; el IVA incluido no se suma otra vez. La foto sin confirmar no modifica el presupuesto.
8. El resumen por fecha conserva productos y precios históricos; la web permite consultar la imagen y descargar el detalle en `.txt` con sesión autorizada.

El OCR local Python sigue como opción de desarrollo con Pillow, pytesseract/Tesseract y OpenCV opcional para sombras. No es el motor utilizado por el despliegue web en Vercel.

## Fotografías y precios de ofertas

`catalog_search.py` consulta catálogos públicos de Día, Coto, Carrefour, Vea y Jumbo y extrae precio, marca, disponibilidad, enlace y la fotografía de la variante (`imageUrl` en VTEX; `image_url` en Coto). La API entrega `image_url` y los clientes muestran esa fotografía real junto con su fuente. Si la imagen falta o deja de estar disponible, la interfaz lo informa. No se generan imágenes ni precios con IA. Ratoneando es un enlace de consulta y un proveedor opcional sujeto a autorización; no hay cobertura garantizada de todas las tiendas.

## Verificación y límites

Las pruebas locales usan almacenamiento temporal y fotos sintéticas. La foto real de DIA se prueba únicamente cuando se indica su ruta local mediante `E2E_RECEIPT_FIXTURE`; no se incorpora a Git ni se registra en el hogar publicado. Un carácter ambiguo como la letra L frente al número 1 puede requerir corrección manual. Las advertencias no se presentan como un porcentaje de exactitud ni como garantía sobre cualquier foto.

La cuenta publicada del hogar es compartida y contiene información cargada por usuarios; las pruebas que escriben compras se ejecutan en entornos locales ficticios. Ver [presentación](Presentacion_Expensas-House.md), [informe breve](INFORME_PRESENTACION.md) y [cuadernillo](../CUADERNILLO_TECNICO_IA.md).

Actualización de ofertas: Día, Carrefour, Vea y Jumbo utilizan sus catálogos públicos VTEX; Coto se consulta mediante la búsqueda pública usada por su tienda. En Coto se compara el precio de una unidad en la sucursal 200, sin aplicar descuentos que exigen varias unidades o un medio de pago. Las fotografías provienen del catálogo correspondiente. La recomendación top es el menor precio entre presentaciones comparables, excluyendo otros tamaños y presentaciones sin confirmar cuando la consulta especifica peso o volumen. Android muestra dos tarjetas por fila y reserva las condiciones y la fuente para el detalle ampliable.
