# Resultado local de regresión · 28/10/2026

| Capa | Ejecución | Resultado |
|---|---|---|
| API | pytest, datos temporales | 46 pruebas y 31 subtests aprobados |
| Web | Playwright, Chromium, API real aislada | 4 escenarios aprobados |
| Android | Compose/JUnit en teléfono conectado por USB | 1 escenario de error de conexión y recuperación aprobado |
| Compilación Android | assembleDebug + assembleDebugAndroidTest | Aprobada |
| HTTPS temporal | Estado público y consulta de gastos sin sesión | HTTP 200 y HTTP 401 respectivamente |

Se instaló el APK actualizado en el teléfono sin borrar los datos de la app. Los escenarios automatizados usan datos sintéticos o repositorios simulados. La prueba manual de cámara/galería con fotografías reales y una sesión autenticada sigue pendiente.

La evidencia JUnit/HTML de API y web se genera en `test-results` y `playwright-report`, excluidos de Git. El workflow genera nuevos resultados de CI tras cada ejecución; este documento no afirma que CI haya pasado.
