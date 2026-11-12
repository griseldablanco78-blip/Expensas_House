# Escáner de tickets, productos comprados y búsqueda de precios

Actualización: 12 de noviembre de 2026.

## Diagnóstico de conectividad y despliegue

El despliegue anterior tenía `framework=fastapi` en la raíz, pero Vercel no encontraba el punto de entrada (`FASTAPI_ENTRYPOINT_NOT_FOUND`). Además, la configuración estática de la web no reenviaba `/api` al backend. La API local estaba apagada y el dominio temporal anterior no resolvía. En esas condiciones no pueden funcionar el login, el escaneo ni la búsqueda.

La publicación de pruebas sirve el frontend de `frontend/web` y reenvía `/api` a una API HTTPS de demostración. Es una arquitectura de pruebas: el backend y sus archivos permanecen en la PC, por lo que deben seguir activos la PC, la API y el túnel. Una URL de Vercel no hace persistentes ni ejecuta automáticamente SQLite, JSON o Tesseract de esta instalación. Un despliegue permanente requiere migrar esos componentes o usar un servidor persistente.

## Tecnología y modelo del escáner

El lector utiliza **Tesseract 5** mediante `pytesseract`, con el motor neuronal **LSTM** seleccionado explícitamente por `--oem 1`. El entorno de demostración incorpora los modelos oficiales `spa.traineddata` y `eng.traineddata` de `tessdata_fast`, usando `spa+eng`. Los modelos se conservan localmente, fuera de Git; no se entrenó un modelo propio.

**Pillow** orienta la foto según EXIF y prepara escala/contraste/márgenes sin recortar sus bordes. **OpenCV** aplica umbral adaptativo en el modo opcional de fotos con sombras. Después del OCR, reglas Python interpretan nombres, cantidades y precios. El borrador se revisa antes de generar un gasto. No se utilizan ChatGPT, Gemini ni una API externa de visión para leer las fotos.

Referencia: [motor y modelos de Tesseract](https://tesseract-ocr.github.io/tessdoc/).

## Formatos y almacenamiento

| Etapa | Formato y ubicación |
|---|---|
| Foto de entrada | JPG, PNG o WebP; hasta 10 MB y 25 megapíxeles. PDF no está implementado. |
| Envío de foto | HTTP multipart, campo `image`, a `/api/receipts/scan`. |
| Salida OCR | Texto UTF-8 y borrador JSON con productos, cantidades, precios y advertencias. |
| Revisión/confirmación | JSON validado por Pydantic en `/api/receipts/confirm`. |
| Imagen archivada | JPEG completo, orientado y sin EXIF; nombre aleatorio privado. |
| Gasto confirmado | JSON con supermercado, fecha, detalle por producto, total, texto e imagen asociada. |
| Descarga de lectura | Archivo `.txt` con texto reconocido y detalle revisado. |

En el modo estándar los registros están en `data/app_state.json` y las imágenes en `data/receipts`. El modo de demostración separa esos archivos en `.runtime/demo`; no usa los gastos ni las cuentas personales del hogar. Ninguno de esos archivos privados se publica en GitHub.

## Tabla de productos comprados

El mes seleccionado muestra supermercado, producto, detalle opcional, cantidad, precio unitario, descuento de la línea e importe neto.

`importe neto = cantidad × precio unitario − descuento de la línea`

El descuento se ingresa como importe monetario total de esa fila, no como porcentaje. Un descuento general del comprobante que no pueda asignarse a un producto se registra como ajuste con explicación. El backend comprueba la relación entre cantidad, precio, descuento y neto, y compara la suma de productos con el total del ticket.

La confirmación guarda el gasto y descuenta del presupuesto de referencia el total del mes. La web cambia al mes de la compra, de modo que un ticket de un mes anterior aparece inmediatamente después de guardarse. Corregir el texto reconocido conserva la imagen asociada. Reenviar el mismo identificador no duplica el gasto; volver a escanear como un ticket nuevo todavía requiere revisión.

## Búsqueda de precios

Las ofertas guardadas siguen disponibles. `EXPENSA_LIVE_OFFERS=1` habilita consultas a los catálogos públicos de Carrefour y Jumbo, con llamadas paralelas, límite de respuesta, timeout y caché de cinco minutos. Se usan precio, disponibilidad, marca, fotografía, enlace y precio de lista publicados por cada fuente; no se generan precios con IA.

Las consultas con espacios se codifican como `%20`, porque los catálogos verificados rechazaban el signo `+` con HTTP 400. La búsqueda inicial es amplia (`leche`) y la comparación posterior conserva el filtrado por nombre y presentación. Si una fuente falla o restringe el acceso, queda un aviso visible y se mantienen los resultados de otras fuentes. El resultado no garantiza disponibilidad, precio por sucursal ni promociones de fidelidad.

Ratoneando continúa como adaptador opcional de una instancia autorizada configurada en `RATONEANDO_API_URL`; sin esa configuración no representa una búsqueda en vivo. No hay cobertura implementada de todos los supermercados.

Referencia del formato: [Search API de VTEX](https://developers.vtex.com/docs/api-reference/search-api).

## Cuenta y regresión de pruebas

El entorno aislado usa el usuario `test123` y la contraseña `PruebasTest1234`, solicitados para pruebas. Son credenciales compartidas de demostración: se utilizan únicamente con datos ficticios. Las demás cuentas conservan sus reglas de acceso.

La regresión comprueba descuentos/netos, cantidades decimales, metadatos conservados, gasto mensual, errores de infraestructura, fallas parciales de fuentes y lectura OCR sobre una imagen sintética. La precisión sobre un ticket real requiere contrastar el resultado con la imagen original.
