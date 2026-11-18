# Actualización: tickets y detalle de ofertas

## Lectura de comprobantes

La imagen completa se conserva como comprobante. Android reconoce el texto con ML Kit y la web con Tesseract.js y su modelo español. El servidor interpreta ese texto mediante reglas; no se entrenó un modelo propio para adivinar importes.

La revisión conserva descripción, precio unitario, descuento e importe neto. La cantidad permite calcular compras de varias unidades o por peso. Los encabezados fiscales, direcciones y medios de pago no se consideran productos. Las descripciones partidas se unen. Si una línea contiene precio unitario y neto, se obtiene el descuento por diferencia. Un descuento identificado como «producto» se propone sobre el renglón anterior, con advertencia. Los descuentos generales ambiguos requieren revisión y ajuste manual.

El IVA es un dato separado y opcional: vacío significa que no se reconoció, no que sea cero. Por defecto se considera incluido en los precios. Si está separado, debe indicarse expresamente. El total pagado del comprobante es el importe registrado y descontado del presupuesto; el IVA incluido no se suma otra vez. El identificador del ticket evita duplicar el gasto al reintentar. Los cambios no recalculan comprobantes anteriores.

## Ofertas en Android

La pantalla incorpora el resumen de comparación de la API, el menor precio publicado, el descuento informado, las condiciones y la información de stock disponible. Cada tarjeta permite abrir su detalle: marca, presentación, precio de referencia y fecha de la fuente cuando existen. «Ver más ofertas» permite consultar resultados posteriores a los diez iniciales. La comparación requiere revisar presentación y vigencia en el supermercado.

## Verificación

Las pruebas utilizan datos ficticios locales: exclusión de encabezados, descripciones partidas, descuentos, varias tasas de IVA, IVA incluido y separado, registro del presupuesto y reintento sin duplicar. Playwright comprueba el flujo web; las pruebas instrumentadas de Compose verifican el resumen y el detalle de ofertas en Android. La precisión sobre tickets reales depende de la nitidez y del formato del comercio; no se declara un porcentaje de acierto sin una muestra evaluada.
