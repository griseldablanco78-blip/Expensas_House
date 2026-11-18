# Actualización: tickets y detalle de ofertas

## Lectura de comprobantes

La imagen completa se conserva como comprobante. Android reconoce el texto con ML Kit y la web con Tesseract.js y su modelo español. El servidor interpreta ese texto mediante reglas; no se entrenó un modelo propio para adivinar importes.

La revisión conserva descripción, precio unitario, descuento e importe neto. La cantidad permite calcular compras de varias unidades o por peso. Los encabezados fiscales, direcciones y medios de pago no se consideran productos. Las descripciones partidas se unen. Si una línea contiene precio unitario y neto, se obtiene el descuento por diferencia. Un descuento identificado como «producto» se propone sobre el renglón anterior, con advertencia. Los descuentos generales ambiguos requieren revisión y ajuste manual.

El IVA es un dato separado y opcional: vacío significa que no se reconoció, no que sea cero. Por defecto se considera incluido en los precios. Si está separado, debe indicarse expresamente. El total pagado del comprobante es el importe registrado y descontado del presupuesto; el IVA incluido no se suma otra vez. El identificador del ticket evita duplicar el gasto al reintentar. Los cambios no recalculan comprobantes anteriores.

## Ofertas en Android

La pantalla incorpora el resumen de comparación de la API, el menor precio publicado, el descuento informado, las condiciones y la información de stock disponible. Cada tarjeta permite abrir su detalle: marca, presentación, precio de referencia y fecha de la fuente cuando existen. «Ver más ofertas» permite consultar resultados posteriores a los diez iniciales. La comparación requiere revisar presentación y vigencia en el supermercado.

## Verificación

Las pruebas utilizan datos ficticios locales: exclusión de encabezados, descripciones partidas, descuentos, varias tasas de IVA, IVA incluido y separado, registro del presupuesto y reintento sin duplicar. Playwright comprueba el flujo web; las pruebas instrumentadas de Compose verifican el resumen y el detalle de ofertas en Android. La precisión sobre tickets reales depende de la nitidez y del formato del comercio; no se declara un porcentaje de acierto sin una muestra evaluada.

## Carga y consulta de resúmenes

En la web, «Cargar y leer ticket» abre el selector si todavía no se eligió una imagen. Elegir una foto inicia la lectura y presenta los productos para revisión. No se registra un gasto hasta confirmar. Android distingue «Cargar ticket · foto o galería», que abre el escáner, de «Registrar gasto manual».

El formulario utiliza la descripción del producto sin un campo adicional de detalle. La cantidad se conserva para calcular varias unidades o compras por peso. El cuadro web muestra fecha de compra, supermercado, descripción, cantidad, precio unitario, descuento e importe neto. El mes y la fecha del resumen permiten consultar precios de compras anteriores. Android ofrece también resúmenes por fecha con los productos registrados, IVA y total. Los gastos antiguos que no guardaron productos se identifican sin inventar su detalle.

## Archivo de presentación

`python scripts/crear_zip_presentacion.py` genera `output/Presentacion_Expensas-House.zip` desde la revisión confirmada en Git. Incluye el código, documentación, pruebas y `ENLACES_PROYECTO.txt` con GitHub y Vercel. Excluye archivos locales y verifica la integridad del ZIP. Para regenerarlo con cambios nuevos, deben confirmarse primero en Git.

## Preparación de la imagen en la web

La copia para lectura se amplía cuando el texto es pequeño (con límite de memoria), se convierte a grises, ajusta el contraste y agrega margen blanco sin recortar el ticket. El modo de sombras aplica un umbral local adaptativo en el navegador; no requiere OpenCV. Tesseract prueba distribución por columnas y, si la confianza es baja, una segunda distribución por bloque; se conserva la lectura con mejor indicador de legibilidad. La corrección automática de inclinación ayuda con fotos levemente torcidas. La foto archivada permanece en color. Estos indicadores no equivalen a un porcentaje de exactitud del proyecto ni garantizan recuperar texto borroso.

El intérprete conserva las descripciones aunque el OCR agregue líneas vacías entre el nombre y sus precios. La regresión incluye un comprobante sintético con sombras, nombre partido y dos unidades.
