# Plan y estado de Expensa House

Actualizado: 28 de octubre de 2026.

## Propósito

Ayudar a un hogar a conocer sus existencias, preparar compras y controlar gastos. La web y Android consumen la misma API y deben obtener resultados equivalentes.

## Implementado en el código

- Backend modular FastAPI en `backend/app`, frontend web en `frontend/web` y cliente Android en `app`.
- Stock, compras, presupuesto, gastos y sincronización por solicitudes.
- Cuentas, sesiones y perfiles del hogar actual; acceso por usuario y contraseña como modo predeterminado.
- Comparación de ofertas guardadas y adaptador de proveedor externo opcional.
- Tickets: OCR, texto editable, revisión por producto y guardado de detalle con protección contra reintentos duplicados.
- Chatbot basado en reglas y consultas de datos existentes.

## Correcciones de esta revisión

1. Conservar descripciones del ticket repartidas en varias líneas antes del importe.
2. Mejorar legibilidad OCR con orientación EXIF, escala para letra pequeña, contraste y margen sin recortar la imagen.
3. Mostrar descripciones editables en varias líneas en la web y conservarlas al confirmar.
4. Incorporar alta de ofertas desde la web y prueba de equivalencia con el endpoint Android.
5. Mostrar errores de consulta en el comparador y actualizar la versión de los archivos para evitar caché anterior.
6. Actualizar README y documentación funcional con el alcance actual.

## Módulo contable incorporado

Selector mensual en la web, gastos por supermercado, fecha de compra, saldo, archivo privado de imágenes y descarga del texto con detalle revisado. El escáner se ubica dentro de Presupuesto y gastos. Android conserva texto, fecha e imagen al confirmar. OpenCV se incorpora como lectura opcional para fotos con sombras; Tesseract sigue siendo el motor OCR. Ver [diseño y límites](docs/GASTOS_Y_COMPROBANTES.md).

## Publicación

Repositorio: https://github.com/griseldablanco78-blip/Expensas_House

URL desplegada: **pendiente de publicación y verificación**. Consultar [guía de Vercel](deploy/VERCEL.md). No reemplazar este estado por una dirección supuesta.

## Próximas etapas

- Reproducir el fallo de búsqueda web con la instalación y el producto que presentan el error; comprobar que ambos clientes apuntan al mismo servidor y que el proveedor devuelve ofertas vigentes.
- Validar OCR con fotos reales de tickets completos y medir productos reconocidos, nombres e importes contra una transcripción manual.
- Completar extracción de pantallas y servicios de inventario, compras y presupuesto; reducir `app.js` y `MainActivity`.
- Migrar datos del hogar a almacenamiento relacional con migraciones y respaldos; aislar hogares antes de ofrecer uso multiusuario independiente.
- Mantener backend con almacenamiento persistente y Tesseract; publicar frontend en Vercel mediante proxy de API, comprobar sesiones y HTTPS.
- Registrar histórico antes de evaluar modelos predictivos. No presentar métricas de experimentos como precisión del producto.

## Criterios de aceptación

Una búsqueda equivalente muestra el mismo producto/precio en web y Android; una falla externa deja un mensaje visible. Un ticket permite revisar y guardar nombres completos, cantidades, precios y total; un reintento no duplica el gasto. Los usuarios de lectura no pueden modificar datos. La URL pública debe probarse con inicio de sesión y una operación completa antes de anunciarla.

Ver [README](README.md), [arquitectura](docs/ARQUITECTURA.md) y [presentación](docs/Presentacion_Expensas-House.md).
