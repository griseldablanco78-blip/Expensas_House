# Módulo de gastos y comprobantes

## Recorrido

En la web, abrir **Presupuesto y gastos**. Elegir el mes para consultar gastos, saldo y agrupación por supermercado. El escáner está dentro del mismo módulo.

1. Elegir o tomar una foto completa; la vista previa permite revisar los bordes.
2. Usar lectura normal. Si hay sombras, elegir **Foto con sombras · OpenCV** y volver a leer. Instalar previamente `requirements-ocr.txt` en el backend.
3. Revisar el texto, fecha de compra, supermercado, productos, cantidades e importes. La fecha se inicia con el día actual: corregirla si la compra fue otro día. Supermercado y fecha no se deducen automáticamente.
4. Confirmar. Recién entonces se registra el gasto. El OCR no decide movimientos monetarios por sí solo.
5. Consultar el historial del mes; descargar el texto o abrir la imagen de respaldo.

La pantalla Android también envía fecha, texto y referencia del comprobante al confirmar. La selección mensual y las descargas se incorporan en esta entrega a la web; la pantalla histórica Android conserva el comportamiento anterior.

## Qué se conserva y dónde

| Dato | Ubicación actual |
|---|---|
| Texto reconocido y detalle revisado | Registro de gasto en `data/app_state.json` |
| Fecha de compra, supermercado, total e identificador | Mismo registro de gasto |
| Imagen de respaldo completa, orientada y convertida a JPEG | `data/receipts/<identificador aleatorio>.jpg` |
| Archivo de lectura `.txt` | Se genera al descargar desde el registro guardado; incluye texto OCR y detalle revisado |

Las imágenes no se sirven como archivos estáticos públicos. Solo se descargan mediante rutas de la API, con sesión y permisos para consultar gastos. No se suben a GitHub. La imagen se archiva al finalizar la lectura; hasta confirmar no está vinculada a un gasto ni disponible por el historial. Las lecturas abandonadas pueden dejar archivos sin referencia: la limpieza y política de retención quedan pendientes.

Respaldar juntos `data/app_state.json`, `data/accounts.sqlite3` y `data/receipts`. En producción se requiere un volumen persistente o migración a almacenamiento externo privado; un despliegue estático no guarda estos datos.

## Cálculos

`gasto del mes = suma de gastos cuya fecha de compra pertenece al mes`

`saldo = presupuesto de referencia configurado - gasto del mes`

Para registros anteriores sin fecha de compra se usa el timestamp, convertido a horario argentino (UTC−03:00). No se borra el historial al cambiar de mes. Un identificador de ticket confirmado protege frente al reintento del mismo envío; volver a escanearlo como un ticket nuevo todavía requiere revisión para evitar cargarlo dos veces.

El presupuesto configurado es una referencia común, no un presupuesto histórico distinto guardado por mes. El endpoint anterior sin mes conserva el acumulado para compatibilidad con Android y sincronización. La web usa `/api/budget?month=AAAA-MM`; Boti House consulta el mes actual. No hay conexión con bancos, tarjetas ni importación de resúmenes en esta etapa.

## Herramientas gratuitas

- **Tesseract:** motor OCR abierto; convierte imagen en texto. [Documentación](https://tesseract-ocr.github.io/tessdoc/).
- **OpenCV:** procesamiento de imágenes; el modo opcional usa umbral adaptativo para fondos desiguales. No sustituye a Tesseract ni garantiza recuperar texto cortado o borroso. [Umbral adaptativo](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html).
- **Pillow:** orientación, escala, contraste y archivo de imágenes en el flujo normal.
- **JSON y SQLite:** almacenamiento local actual; no requieren contratar un servicio.
- **Supabase:** alternativa futura de PostgreSQL y almacenamiento privado con plan gratuito sujeto a límites e inactividad. No está integrado; requiere migrar el acceso a datos y permisos. [Plan vigente](https://supabase.com/pricing).

Instalación avanzada: `.venv/Scripts/python.exe -m pip install -r requirements-ocr.txt`. Tesseract y sus idiomas se instalan aparte. No se envían fotos a un servicio externo de IA en este flujo.

## Verificación y límites

Pruebas de archivo, descarga protegida, fecha, resumen mensual, límites de mes en horario argentino y reintentos. La calidad OCR debe medirse con fotos reales; una prueba con OCR simulado comprueba el circuito y no demuestra precisión sobre tickets reales. Una foto recortada no contiene la información que falta: volver a fotografiar el comprobante completo.
