# Actualización: tickets y detalle de ofertas

## Lectura de comprobantes

La imagen completa se conserva como comprobante. Android reconoce el texto con ML Kit y la web con Tesseract.js y su modelo español. El servidor interpreta ese texto mediante reglas; no se entrenó un modelo propio para adivinar importes.

La revisión conserva descripción, precio unitario, descuento e importe neto. La cantidad permite calcular compras de varias unidades o por peso. Los encabezados fiscales, direcciones y medios de pago no se consideran productos. Las descripciones partidas se unen. Si una línea contiene precio unitario y neto, se obtiene el descuento por diferencia. Un descuento identificado como «producto» se propone sobre el renglón anterior, con advertencia. Si el ticket imprime `TOTAL PRODUCTOS` y luego un renglón final `TOTAL`, el backend separa ambos importes: toma `TOTAL` como importe pagado y muestra la diferencia como descuento o ajuste para revisión. Los descuentos generales ambiguos siguen requiriendo cotejo con la foto.

El IVA es un dato separado y opcional: vacío significa que no se reconoció, no que sea cero. Por defecto se considera incluido en los precios. Si está separado, debe indicarse expresamente. El total pagado del comprobante es el importe registrado y descontado del presupuesto; el IVA incluido no se suma otra vez. El identificador del ticket evita duplicar el gasto al reintentar. Los cambios no recalculan comprobantes anteriores.

## Ofertas en Android

La pantalla incorpora el resumen de comparación de la API, el menor precio publicado, el descuento informado, las condiciones y la información de stock disponible. Cada tarjeta permite abrir su detalle: marca, presentación, precio de referencia y fecha de la fuente cuando existen. «Ver más ofertas» permite consultar resultados posteriores a los diez iniciales. La comparación requiere revisar presentación y vigencia en el supermercado.

## Verificación

Las pruebas utilizan datos ficticios locales: exclusión de encabezados, descripciones partidas, descuentos, varias tasas de IVA, IVA incluido y separado, registro del presupuesto y reintento sin duplicar. Playwright comprueba el flujo web; las pruebas instrumentadas de Compose verifican el resumen y el detalle de ofertas en Android. La precisión sobre tickets reales depende de la nitidez y del formato del comercio; no se declara un porcentaje de acierto sin una muestra evaluada.

## Carga y consulta de resúmenes

En la web, «Cargar y leer ticket» abre el selector si todavía no se eligió una imagen. Elegir una foto inicia la lectura y presenta los productos para revisión. No se registra un gasto hasta confirmar. Android distingue «Cargar ticket · foto o galería», que abre el escáner, de «Registrar gasto manual».

El formulario utiliza la descripción del producto sin un campo adicional de detalle. La cantidad se conserva para calcular varias unidades o compras por peso. El cuadro web muestra fecha de compra, supermercado, descripción, cantidad, precio unitario, descuento e importe neto. El mes y la fecha del resumen permiten consultar precios de compras anteriores. Android ofrece también resúmenes por fecha con los productos registrados, IVA y total. Los gastos antiguos que no guardaron productos se identifican sin inventar su detalle.

## Archivo de presentación

`python scripts/crear_zip_presentacion.py` genera `output/Presentacion_Expensas-House.zip` desde la revisión confirmada en Git. Incluye únicamente código y TXT con los enlaces de GitHub y Vercel. La APK se publica por separado en GitHub Releases; informes y fotos no se agregan al ZIP. La documentación extensa se consulta en GitHub. Excluye archivos locales y verifica la integridad del ZIP. Para regenerarlo con cambios nuevos, deben confirmarse primero en Git.

## Preparación de la imagen en la web

La copia para lectura se amplía cuando el texto es pequeño (con límite de memoria), se convierte a grises, ajusta el contraste y agrega margen blanco sin recortar el ticket. El modo de sombras aplica un umbral local adaptativo en el navegador; no requiere OpenCV. Tesseract prueba distribución por columnas y por bloque; se conserva la lectura con mejor indicador de legibilidad. La foto archivada permanece en color. Estos indicadores no equivalen a un porcentaje de exactitud del proyecto ni garantizan recuperar texto borroso.

El intérprete conserva las descripciones aunque el OCR agregue líneas vacías entre el nombre y sus precios. La regresión incluye un comprobante sintético con sombras, nombre partido y dos unidades.

## Nombres y presentaciones decimales

La web prepara la copia de OCR desde la imagen original, antes de comprimir el archivo de respaldo, y compara dos distribuciones de lectura en cada foto. El intérprete distingue presentaciones como «2.25L» y «0,50 kg» de los importes. Un fragmento de una sola letra acompañado de signos o cifras no se acepta como nombre de producto. Los nombres que el OCR no logra leer no se completan con marcas inventadas: deben revisarse contra la foto. La reproducción exacta de una falla requiere el ticket original.

## Encabezado y revisión del ticket DIA

El supermercado y la fecha se proponen desde el encabezado reconocido y permanecen editables. La lectura automática prueba corrección de sombras si la primera lectura tiene baja confianza. En el formato DIA, cantidad y precio unitario pueden estar encima del producto; los encabezados de columnas y la alícuota entre paréntesis se excluyen del nombre. Los espacios dentro del importe, como «5498 ,00», se normalizan.

La foto proporcionada permitió reproducir una confusión entre L y 1 en «2,25L». Se advierte cuando la presentación es dudosa y se mantiene editable antes de confirmar. No se asegura exactitud total del OCR. El envío muestra los errores de validación junto al estado y desplaza la vista hasta el mensaje, evitando que un rechazo parezca un botón sin respuesta.
