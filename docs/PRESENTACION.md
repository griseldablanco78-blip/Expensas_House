# Guion para presentar Expensa House

## Apertura (1 minuto)

“Expensa House reúne la despensa, la lista de compras y los gastos del hogar. Busca reducir compras innecesarias y facilitar la revisión de precios. Puede usarse desde Android y desde una web conectados al mismo servidor.”

## Arquitectura (1 minuto)

“El frontend es lo que ve la persona. El backend valida los datos, comprueba permisos y aplica las operaciones. La persistencia conserva el estado. Separarlos permite mantener la interfaz y las reglas de negocio sin duplicarlas entre clientes.”

Mostrar `frontend/web`, `backend/app/api`, `backend/app/services`, `backend/app/infrastructure` y `app`. Explicar que se mantiene un monolito modular y que la migración relacional aún está pendiente.

## Demostración (3 minutos)

1. Iniciar sesión y mostrar stock y unidades abiertas.
2. Agregar un producto y comprobar la lista de compras.
3. Crear una oferta real indicando producto, presentación, supermercado y precio. Buscar ese producto en el comparador. Explicar si la fuente es guardada o externa.
4. Subir un ticket completo; revisar el texto OCR y cada producto. Corregir errores, indicar supermercado y confirmar. Mostrar detalle del gasto y presupuesto disponible.
5. Preguntar al chatbot por saldo o faltantes y mostrar la sección correspondiente.
6. Si Android está conectado al mismo servidor, sincronizar y comparar datos.

Usar un hogar de demostración y productos identificados como tales. Si no está configurado el proveedor, explicar el modo de ofertas guardadas sin prometer búsqueda en vivo.

## Cierre (1 minuto)

“El valor del sistema es reunir operaciones del hogar en una API compartida. El OCR necesita revisión humana. La siguiente etapa es mejorar las mediciones con tickets reales, completar la separación de pantallas y migrar la persistencia para producción.”

Mostrar la URL pública únicamente después de verificar el despliegue. El estado y enlace se mantienen en el README.

## Preguntas frecuentes

- **¿El chatbot es IA generativa?** La implementación actual usa reglas y datos del hogar.
- **¿Los precios están siempre actualizados?** Depende de la fuente y su fecha. Las ofertas guardadas se mantienen manualmente.
- **¿Escanear actualiza el stock?** Actualmente registra el gasto y su detalle; el inventario se gestiona por separado.
- **¿Qué ocurre si falla el OCR?** Se puede corregir el texto, agregar productos y revisar antes de confirmar.
- **¿Por qué backend aparte de Vercel?** Esta versión necesita almacenamiento persistente local y el ejecutable Tesseract.
