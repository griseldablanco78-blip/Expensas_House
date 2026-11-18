# Verificación de tickets, ofertas y resúmenes · 18/11/2026

| Control | Resultado observado |
| --- | --- |
| Backend · pytest | 54 pruebas y 33 subpruebas aprobadas. Una prueba de PostgreSQL omitida porque requiere un entorno ficticio autorizado. |
| Web · Playwright | 11 casos aprobados con servidor local real y almacenamiento temporal. |
| Android · compilación | APK y pruebas instrumentadas compilados con éxito. Versión 1.3.1 instalada conservando los datos del dispositivo. |
| Android · flujos Compose | Tres casos aprobados: botón de carga y filtro de fecha, detalle de ofertas y reintento tras falla de red. |
| Android · OCR | La prueba instrumentada de foto sintética completa aprobó durante la ejecución del mismo APK; los controles Compose se repitieron con la pantalla despierta. |

## Casos incorporados

- Nombres partidos por líneas vacías: se conserva la descripción asociada a cantidad y precio.
- Foto sintética con letra pequeña y sombras: se leen los dos productos completos con sus importes.
- Carga web: el botón abre el selector y elegir la foto inicia la lectura sin registrar automáticamente el gasto.
- IVA incluido y separado, descuentos por línea y reintento del mismo ticket sin duplicar el presupuesto.
- Consulta por fecha: dos compras del mismo producto conservan sus respectivos precios históricos.
- Android: «Cargar ticket» invoca el flujo de escáner; el gasto manual tiene una acción independiente.

La primera ejecución de las pruebas Compose no encontró pantallas con el dispositivo en reposo. Se repitió manteniendo temporalmente la pantalla encendida y se restauró el ajuste original al terminar. La suite web reutiliza una sesión de pruebas para no disparar el límite de intentos de acceso; no se desactiva la protección del servidor.

Las pruebas no modifican gastos personales. Los resultados sobre imágenes sintéticas no constituyen una medición de exactitud sobre tickets reales. Se mantiene la revisión del usuario antes de confirmar importes.

## Ampliación: ticket real DIA y entrega breve

- Backend: 59 pruebas y 36 subpruebas aprobadas; una prueba de PostgreSQL omitida por requerir entorno ficticio autorizado.
- Web: 12 pruebas aprobadas, incluida la foto real de DIA mediante ruta local opcional. La imagen no se publica en GitHub ni se registra en el hogar de producción.
- El caso real comprueba mejora automática de sombras, producto legible, cantidad, precio, supermercado propuesto, IVA y total. La letra L de la presentación puede confundirse con 1: el caso corrige ese carácter durante la revisión antes de confirmar y verifica el gasto de $5.498 en el presupuesto.
- Se evita un descuento ficticio por un precio unitario mal reconocido cuando el comprobante declara descuento cero y los netos coinciden con el total: se propone el unitario calculado y se informa para revisión.
- Android 1.3.2: APK y pruebas compilados; instalada conservando datos. Supermercado y fecha recibidos del backend completan el borrador cuando están disponibles.
- El paquete breve conserva código, TXT de enlaces e informe de seis puntos. APK y foto autorizada se agregan solo al ZIP. La documentación extensa queda en GitHub.

Estos resultados verifican el recorrido con revisión humana; no representan una exactitud del 100% del OCR ni eliminan la necesidad de confirmar datos dudosos.
