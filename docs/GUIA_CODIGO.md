# Guía del código, tecnologías y librerías

## Conceptos básicos

- **Frontend:** pantallas y controles que utiliza la persona. Pide operaciones al servidor.
- **Backend:** recibe esas solicitudes, comprueba quién tiene permiso, valida información y ejecuta operaciones.
- **API:** contrato entre clientes y servidor. Un endpoint es una dirección para una operación, por ejemplo `POST /api/receipts/confirm`.
- **HTTP:** protocolo de las solicitudes. GET consulta; POST crea o ejecuta; PATCH modifica parcialmente.
- **JSON:** formato de texto estructurado para intercambiar datos. No es una base relacional.
- **Librería:** código de terceros que resuelve una tarea concreta. Un framework propone además cómo organizar la aplicación.
- **Repositorio:** objeto que ofrece acceso a datos sin obligar a una pantalla a conocer cómo funciona la red.
- **OCR:** reconocimiento de caracteres de una imagen. No equivale a comprender contablemente un ticket; por eso hay validaciones y revisión humana.

## Mapa de carpetas

```text
backend/app/           API y lógica compartida
  main.py              Ensambla la aplicación
  api/routes/          Operaciones HTTP por módulo
  api/schemas.py       Contratos y validación de entradas
  services/            Reglas y procesos
  core/                Seguridad y configuración de rutas
  infrastructure/      Lectura y escritura de datos
frontend/web/          Cliente de navegador
  index.html           Pantallas y formularios
  css/                 Presentación visual
  js/core/             Utilidades comunes
  js/features/         Interacciones por módulo
  js/app.js            Inicio y pantallas heredadas
app/src/main/          Cliente Android
  java/.../core/       Sesión y construcción de dependencias
  java/.../data/       Room, red y repositorios
  java/.../domain/     Modelos usados actualmente
  java/.../ui/         Componentes, funciones, estado y tema
app/src/androidTest/   Pruebas Android instrumentadas
web/                   Compatibilidad y dashboard opcional
data/                  Adaptadores, EDA y datos locales ignorados
modelos/               Experimento predictivo separado del flujo principal
tests/                 API, navegador, soporte y fixtures sintéticos
scripts/               Configuración y diagnóstico; otros materiales locales no son necesarios
docs/                  Explicaciones, casos y decisiones
deploy/                Ejemplos de infraestructura y publicación
.github/workflows/     Automatización de regresión en GitHub
```

## Backend: qué hace cada archivo principal

| Archivo | Explicación sencilla | Tecnología |
|---|---|---|
| `backend/app/main.py` | Construye la app, registra rutas protegidas y sirve la web. Es el punto de entrada, no el lugar para todas las reglas. | FastAPI, Starlette, python-dotenv |
| `api/schemas.py` | Define qué datos acepta cada operación y restricciones de importes, fechas y campos. | Pydantic |
| `api/routes/auth.py` | Registro, login, contraseñas, cierre de sesión y administración de permisos del hogar. | FastAPI, seguridad central |
| `api/routes/stock.py` | Consultar y modificar existencias y consumo. | FastAPI, persistencia actual |
| `api/routes/shopping.py` | Gestionar pendientes de compra y sus operaciones. | FastAPI |
| `api/routes/budget.py` | Registrar gastos, configurar presupuesto y consultar el resumen mensual. | FastAPI, servicios de reporte |
| `api/routes/offers.py` | Consultar y editar ofertas; guardar fotografías de productos y validar archivos. | FastAPI, Pillow |
| `api/routes/receipts.py` | Recibir foto/texto, pedir lectura, confirmar gasto y descargar comprobantes protegidos. | FastAPI, tareas de lectura fuera del bucle async |
| `api/routes/chat.py` | Recibir mensajes y delegar la respuesta al servicio compartido. | FastAPI |
| `api/routes/voice.py` | Recibir audio para transcripción donde el entorno lo permita. | SpeechRecognition; proveedor depende de configuración |
| `api/routes/sync.py` | Intercambiar estado con Android sin permitir saltar los permisos. | JSON y servicio de sincronización |
| `api/routes/legacy.py` | Mantener rutas anteriores para no romper clientes existentes. | Adaptador de compatibilidad |
| `services/offers.py` | Limpiar consultas, comparar ofertas compatibles y contestar el chatbot mediante reglas. | urllib, expresiones regulares, normalización Unicode |
| `services/receipt_scanning.py` | Orientar y mejorar imagen, ejecutar OCR, interpretar líneas e importes y producir un borrador para revisión. | Pillow, pytesseract, Tesseract; OpenCV opcional |
| `services/receipt_registration.py` | Comprobar cantidades/totales y evitar duplicar gasto cuando se reenvía el mismo ID. | Servicio Python, redondeo decimal |
| `services/receipt_archive.py` | Archivar la imagen completa como JPEG con nombre aleatorio y validar referencias de archivo. | Pillow, pathlib, secrets |
| `services/expense_reporting.py` | Elegir gastos por mes y sumar totales por supermercado y saldo. | datetime, zona horaria argentina, collections |
| `services/snapshot_merge.py` | Comparar estado base, cambios del teléfono y cambios del servidor para preservar datos o informar conflicto. | Python, deepcopy |
| `services/synchronization.py` | Coordinar la combinación y persistencia de la sincronización. | Servicio de aplicación |
| `core/security.py` | Cuentas, contraseñas cifradas mediante hash, sesiones y permisos verificados en servidor. | SQLite, Argon2, secrets; SMTP en modo opcional |
| `core/http_security.py` | Exigir HTTPS fuera del desarrollo local, validar orígenes y agregar cabeceras de protección. | Middleware Starlette |
| `core/paths.py` | Resolver ubicaciones desde el proyecto sin depender del directorio de ejecución. | pathlib |
| `infrastructure/json_store.py` | Leer/escribir datos del hogar y mantener exportaciones heredadas. Usa un bloqueo dentro del proceso. | JSON, threading, pandas |

Los archivos `__init__.py` identifican paquetes de Python; no representan módulos de negocio adicionales. El bloqueo de JSON no reemplaza una base transaccional para producción con múltiples procesos.

## Frontend web

| Archivo | Qué hace |
|---|---|
| `index.html` | Estructura las secciones, formularios, etiquetas y navegación. |
| `css/style.css` | Colores, tamaño, distribución, tablas y adaptación de pantalla. |
| `css/polish.css` | Ajustes visuales complementarios. |
| `js/core/auth.js` | Inicio de sesión, usuario actual, presentación según permisos y envío de protección CSRF en solicitudes. Ocultar un botón no sustituye al permiso del servidor. |
| `js/core/dom.js` | Escapar textos y validar enlaces antes de insertarlos en la interfaz. |
| `js/features/offers.js` | Buscar ofertas, renderizar resultados y crear/editar ofertas guardadas. |
| `js/features/chat.js` | Abrir conversación, enviar mensajes y navegar a la sección indicada. |
| `js/features/receipts.js` | Seleccionar/ver foto, pedir lectura, editar borrador y conservar un envío pendiente para reintentar sin cambiar su ID. |
| `js/features/expenses.js` | Mostrar gastos del mes y enlaces privados a texto e imagen del comprobante. |
| `js/app.js` | Iniciar componentes, cargar datos, cambiar pestañas y gestionar formularios de inventario/compras/presupuesto que aún no se extrajeron. |

Se usa JavaScript del navegador, sin React ni compilación obligatoria. `fetch` comunica con la API; `localStorage` conserva preferencias y borradores, no contraseñas ni tokens de sesión. La cookie de sesión HTTP-only la administra el navegador. Web Speech API depende del soporte y permisos del navegador.

## Cliente Android

| Carpeta/archivo | Qué hace | Librerías |
|---|---|---|
| `ExpensaApp.kt` | Inicia componentes de aplicación y base local. | Android Application, Room |
| `MainActivity.kt` | Aloja la interfaz y navegación; contiene partes heredadas pendientes de extraer. | Kotlin, Compose, Material 3 |
| `core/auth/AuthSession.kt` | Mantiene la sesión actual en memoria. | StateFlow/estado Kotlin |
| `core/di/AppContainer.kt` | Construye repositorios y dependencias concretas que usarán las pantallas. | Inyección manual de dependencias |
| `data/remote/ExpensaApi.kt` | Contratos Retrofit, URL base, tiempos de espera, HTTPS y envío del token de sesión. | Retrofit, OkHttp, Gson |
| `data/remote/ApiModels.kt` | Datos enviados/recibidos por red: borrador de ticket, confirmación, oferta y sincronización. | Kotlin data classes, Gson |
| `data/remote/SupermarketApi.kt` | Contrato heredado de consulta de ofertas. | Retrofit |
| `data/local/ExpensaDatabase.kt` | Base local y operaciones de acceso a existencias y otros datos Android. | Room |
| `data/repository/` | Interfaces y adaptadores de ofertas, chat y tickets. Permiten usar una implementación de red o una falsa en las pruebas. | Patrón repositorio |
| `domain/model/Models.kt` | Modelos actuales del inventario, compras y gastos. Algunos también están vinculados a persistencia: separación pendiente. | Kotlin, anotaciones Room |
| `ui/features/auth/` | Pantalla de ingreso y manejo de cuenta. | Compose |
| `ui/features/offers/` | Consulta y presentación de ofertas. | Compose, repositorio |
| `ui/features/chat/` | Conversación con Boti House y acciones disponibles. | Compose, repositorio |
| `ui/features/receipts/` | Cámara/galería, revisión de líneas, fecha y confirmación del gasto. | Activity Result API, FileProvider, corrutinas |
| `ui/components/` | Controles reutilizables de dictado, imagen de oferta y mensajes de error. | Compose, APIs Android |
| `ui/viewmodel/ExpensaViewModel.kt` | Estado y eventos de los módulos actuales; coordina operaciones y sincronización. | ViewModel, Coroutines, StateFlow |
| `ui/theme/` | Colores y tema de la interfaz. | Material 3 |
| `res/xml/ticket_photo_paths.xml` | Limita qué archivos temporales de cámara puede compartir la app mediante FileProvider. | Android XML |

MVVM significa separar pantalla (View), estado/coordinación (ViewModel) y datos (Model). El proyecto se acerca a ese esquema incrementalmente; algunas operaciones del escáner todavía viven en Compose y mantienen una separación parcial de responsabilidades.

## Análisis y compatibilidad

`web/api.py`, `web/receipts.py`, `web/offer_service.py`, `web/sync_service.py` y `data/db.py` redirigen importaciones antiguas a implementaciones nuevas. Evitan mantener dos reglas de negocio distintas.

`web/dashboard.py` y `web/app_streamlit.py` son superficies de análisis opcionales. `data/generar_dataset.py` genera material para análisis; `data/eda.py` prepara exploración; `modelos/modelo_prediccion.py` contiene un experimento con scikit-learn. Esas piezas no significan que un modelo predictivo controle el inventario o que esté integrado al OCR del producto.

## Pruebas y configuración

- `tests/test_architecture.py`: contratos y compatibilidad al organizar carpetas.
- `tests/test_security.py`: sesiones, perfiles, permisos y protecciones.
- `tests/test_password_accounts.py`: acceso por usuario/contraseña.
- `tests/test_workflows.py`: tickets, ofertas, presupuestos y sincronización.
- `tests/e2e/household.spec.js`: acciones reales del navegador con API aislada.
- `tests/support/e2e_server.py`: entorno temporal y cuenta ficticia solo para pruebas.
- `tests/fixtures/ticket-sintetico.png`: comprobante inventado para OCR reproducible.
- `app/src/androidTest/.../ReceiptRegressionTest.kt`: escenario Android de desconexión/recuperación.
- `pytest.ini`, `playwright.config.js`: selección de pruebas, servidor y reportes.
- `.github/workflows/regression.yml`: ejecuta la regresión al cambiar el repositorio.
- `requirements*.txt`: dependencias Python normales, OCR opcional y pruebas.
- `package.json`/`package-lock.json`: herramientas de prueba web y versiones resueltas.
- `.env.example`: variables de configuración sin credenciales.
- `scripts/crear_administradora.py`: configura el primer acceso local sin contraseña predeterminada.
- `scripts/configurar_correo.py`: configuración opcional de envío de correo.
- `scripts/diagnosticar_conexion.py`: detecta URL vencida o servidor caído antes de investigar OCR.
- `deploy/`: ejemplos y condiciones de publicación; no es evidencia de despliegue activo.

## Ejemplo de recorrido del código

Al confirmar un ticket desde la web: el botón definido en `index.html` dispara `features/receipts.js`; este envía JSON a `/api/receipts/confirm`. `schemas.py` valida el formato, `security.py` exige sesión y permiso, la ruta delega en `receipt_registration.py`, y el servicio verifica importes y registra el gasto mediante `json_store.py`. Al consultar un mes, `expense_reporting.py` calcula el total y `features/expenses.js` lo presenta. El navegador nunca decide por sí solo el gasto oficial del hogar.
