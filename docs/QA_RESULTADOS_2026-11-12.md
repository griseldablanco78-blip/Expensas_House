# Resultados de regresión · 12/11/2026

| Entorno | Verificación | Resultado |
|---|---|---|
| Backend local aislado | pytest, contratos, descuentos/netos, OCR, catálogo, permisos y sincronización | 50 pruebas aprobadas |
| Navegador local | Playwright + API temporal real | 6 escenarios aprobados |
| Vercel público | Login con cuenta autorizada; búsqueda de leche entera; foto sintética; descuento; registro de gasto; comprobantes | 1 escenario completo aprobado; 37 resultados de catálogo visibles en esa consulta |
| Android | Compilación de APK y pruebas instrumentadas | Versión 1.1.0 instalada por USB sin borrar datos; 1 prueba instrumentada aprobada en el teléfono |

URL verificada: https://expensas-house-griselda-blanco.vercel.app

El ensayo público se ejecuta con `npx playwright test --config=playwright.public.config.js`. Solo admite un servidor que responda `mode=demo`; genera un gasto ficticio en el entorno compartido. No debe ejecutarse contra datos personales. Usa la imagen sintética versionada en `tests/fixtures`, no el ticket real de una persona.

El frontend está alojado en Vercel. La API, modelos OCR y datos de demostración siguen en la PC mediante un túnel HTTPS temporal. Estas pruebas no certifican disponibilidad permanente ni precisión con cualquier fotografía de supermercado. No se afirma éxito de CI sin revisar su ejecución.
