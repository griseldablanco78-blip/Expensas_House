# Regresión y automatización de Expensa House

## Alcance y herramientas

- **Backend compartido por web y Android:** pytest ejecuta las pruebas de cuentas, permisos, servicios y API con FastAPI TestClient/HTTPX. Mantiene las pruebas unittest existentes sin reescribirlas.
- **Frontend web:** Playwright + Chromium contra una API real y aislada, con cuenta y hogar temporales. No requiere contraseñas del hogar real.
- **Android:** JUnit + Compose UI Test, con repositorio simulado para comprobar error de conexión y recuperación sin registrar compras reales.
- **CI:** GitHub Actions en push a main/codex y pull requests, o ejecución manual. Publica reportes JUnit, HTML, capturas y trazas web cuando hay fallas; Android publica resultados del emulador.

Son herramientas de un flujo profesional de QA. La elección no implica que todas las empresas usen o exijan la misma combinación. Postman puede complementar exploración de API; no es necesario duplicar automáticamente cada prueba existente en otra herramienta.

## Casos prioritarios

| ID | Preparación y pasos | Resultado esperado | Automatización |
|---|---|---|---|
| API-01 | Consultar datos sin sesión | HTTP 401; no revelar gastos | tests/test_security.py |
| API-02 | Ingresar con perfil de inventario y solicitar comprobante | HTTP 403 | tests/test_security.py |
| API-03 | Confirmar dos veces el mismo identificador de ticket | Un gasto y un descuento | tests/test_workflows.py |
| API-04 | Cargar fecha inválida o presupuesto negativo | HTTP 422 y sin modificación | tests/test_workflows.py |
| API-05 | Consultar meses distintos, incluyendo medianoche argentina | Cada gasto en su mes; saldo correcto | tests/test_workflows.py |
| API-06 | Archivar imagen, confirmar y descargar imagen/texto | Imagen completa, texto y detalle conservados | tests/test_workflows.py |
| WEB-01 | Iniciar sesión; interpretar texto; revisar; confirmar; cambiar mes | Detalle descargable y presupuesto descontado solo en el mes de compra | tests/e2e/household.spec.js |
| WEB-02 | Elegir foto; simular caída de red; leer | Error visible, selección conservada y posibilidad de reintentar | tests/e2e/household.spec.js |
| WEB-03 | Crear oferta y buscar producto/presentación | Resultado del servidor visible en comparador | tests/e2e/household.spec.js |
| WEB-04 | Elegir foto sintética legible y leer con Tesseract | Dos productos y total 2700 para revisión | tests/e2e/household.spec.js |
| AND-01 | Simular dominio no disponible; interpretar; recuperar conexión y reintentar | Mensaje explicativo y producto reconocido; no registrar sin confirmar | ReceiptRegressionTest.kt |
| MAN-01 | Cámara física y galería en teléfono; imagen completa con iluminación real | Foto sube, productos y total revisables; confirmar con cuenta de prueba | Manual pendiente |
| MAN-02 | Reiniciar PC/túnel y probar APK con URL antigua | Diagnóstico identifica dominio no disponible; actualizar URL/APK | Diagnóstico + manual |

Los tests de servidor no prueban el selector de galería ni la cámara física. La prueba Android usa texto y un repositorio simulado; no certifica una subida real por red. WEB-04 usa OCR real sobre una imagen sintética, no mide precisión con fotografías de supermercados.

## Ejecutar

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-test.txt
.venv/Scripts/python.exe -m pytest --junitxml=test-results/api.xml
npm ci
npx playwright install chromium
$env:E2E_PYTHON='.venv/Scripts/python.exe'
npm run test:web
```

`npm run test:web:report` abre el informe HTML. El servidor Playwright solo escucha en `127.0.0.1:18765`, usa un directorio temporal y rechaza arrancar sin su bandera de pruebas. No configurar estos tests contra un hogar real. Los escenarios de red fallida y Android simulan fallas explícitamente; no deben confundirse con validación de infraestructura externa.

Android con emulador desechable:

```powershell
.\gradlew.bat :app:assembleDebugAndroidTest :app:connectedDebugAndroidTest --console=plain
```

En un teléfono con datos personales, no usar tareas que limpien/desinstalen la app. En esta verificación se instalaron APK y APK de pruebas con `adb install -r` y se ejecutó instrumentación sin desinstalación ni limpieza de datos.

## Diagnóstico de conectividad del incidente

La captura del 28/10/2026 mostró una falla de conexión antes de OCR. La API local respondía; el dominio temporal compilado en Android ya no resolvía. Se creó un nuevo túnel HTTPS con autorización explícita, se actualizó la configuración local y se instaló el APK actualizado por USB. Estos enlaces dependen de que la PC, la API y cloudflared permanezcan activos; no son un despliegue permanente.

```powershell
.venv/Scripts/python.exe scripts/diagnosticar_conexion.py
```

El diagnóstico prueba disponibilidad pública y rechazo de lectura de gastos sin sesión. No imprime contraseñas ni consulta gastos privados.

## Evidencia y criterio de salida

Cada falla debe registrar: ID del caso, versión/commit, entorno, pasos, esperado, observado y evidencia sin datos privados. Dar por terminada una regresión únicamente cuando pasen sus controles requeridos; indicar los casos manuales pendientes y distinguir resultados locales de resultados de CI.

Documentación de referencia: [pytest y unittest](https://docs.pytest.org/en/stable/how-to/unittest.html), [servidor de Playwright](https://playwright.dev/docs/test-webserver), [trazas de Playwright](https://playwright.dev/docs/trace-viewer), [pruebas Compose](https://developer.android.com/develop/ui/compose/testing).
