# Expensa House

Aplicación para organizar la despensa del hogar, preparar compras, comparar ofertas y registrar gastos a partir de tickets. Tiene dos clientes: web y Android, conectados a una API Python compartida.

## Documentación del proyecto

[Presentación y ejecución del proyecto](docs/Presentacion_Expensas-House.md) y la [explicación de módulos, tecnologías y librerías](docs/GUIA_CODIGO.md).

[Cuadernillo técnico: modelos, APIs, métricas y mejoras futuras](CUADERNILLO_TECNICO_IA.md). Incluye hogares colaborativos con permisos y prioridades para una versión comercial.

## Enlaces

- [Repositorio](https://github.com/griseldablanco78-blip/Expensas_House)
- [Plan y estado del proyecto](PLAN_PROYECTO.md)
- [Aplicación pública](https://expensas-house-griselda-blanco.vercel.app) · cuenta compartida con datos cargados desde Android. Web y API en Vercel; base e imágenes privadas en Supabase. Quien use las credenciales compartidas puede consultar y modificar ese hogar.
- [Documentación OpenAPI](https://expensas-house-griselda-blanco.vercel.app/docs) y [arquitectura de despliegue](docs/DESPLIEGUE_NUBE.md).
- Desarrollo local: http://localhost:8000 · API interactiva: http://localhost:8000/docs

## Organización y responsabilidades

| Carpeta | Responsabilidad |
|---|---|
| `frontend/web/` | HTML, CSS y JavaScript del navegador. Presenta datos y llama a `/api`; no almacena secretos ni decide permisos. |
| `backend/app/api/` | Rutas HTTP y validación de los contratos de entrada. |
| `backend/app/services/` | Reglas de ofertas, lectura y registro de tickets, sincronización. |
| `backend/app/infrastructure/` | Adaptadores locales y PostgreSQL/Storage para Vercel y Supabase. |
| `backend/app/core/` | Rutas, autenticación, sesiones, permisos y protección HTTP. |
| `app/` | Cliente Android Kotlin, Compose, Room y repositorios de red. |
| `web/`, `data/db.py` | Compatibilidad con importaciones anteriores y dashboard Streamlit opcional. |
| `tests/` | Pruebas de API, permisos, cuentas y flujos. |
| `docs/`, `deploy/` | Arquitectura, exposición y guía de publicación. |

Se utiliza un monolito modular. Frontend y backend están separados en el código, aunque FastAPI puede servir ambos bajo el mismo dominio. La separación es incremental: algunas rutas aún acceden directamente a persistencia y `app.js` conserva varias pantallas. Ver [arquitectura](docs/ARQUITECTURA.md).

## Funcionalidades y límites actuales

- **Despensa:** stock, unidades en uso y lista de reposición.
- **Compras y presupuesto:** selector mensual web, total gastado, saldo y resumen por supermercado. El presupuesto es una referencia común para el mes elegido.
- **Ofertas:** consulta ofertas guardadas; con `EXPENSA_LIVE_OFFERS=1` también consulta catálogos públicos de Carrefour/Jumbo. Ratoneando permanece como proveedor opcional configurado por `RATONEANDO_API_URL`. La web permite agregar y editar ofertas reales. No hay monitoreo automático garantizado de supermercados.
- **Tickets:** tabla de productos por supermercado con detalle, precio unitario, descuento e importe neto; foto JPG/PNG/WebP o texto; OCR con Tesseract, revisión editable y confirmación del gasto con detalle. Conserva nombres en varias líneas, fecha, supermercado, texto reconocido e imagen privada de respaldo; permite descargar un archivo de lectura `.txt`. OpenCV ofrece un modo opcional para fotos con sombras. El OCR puede cometer errores y no recupera palabras ausentes en una foto cortada. Registrar el gasto no implica ingreso automático al stock.
- **Boti House:** consultas de ofertas, presupuesto y faltantes mediante reglas sobre datos del hogar. No se presenta como un modelo generativo entrenado.
- **Android y web:** comparten API; la sincronización depende de conexión y solicitudes, no de un canal de tiempo real.
- **Android 1.2.0:** usa la dirección fija de Vercel. ML Kit Text Recognition v2 con modelo latino incluido lee la foto en el teléfono; el servidor interpreta el texto y conserva el comprobante revisado. No requiere una API de IA de pago.
- **Acceso:** por defecto usuario y contraseña (`EXPENSA_AUTH_MODE=password`). El modo de correo verificado es opcional y requiere SMTP. Los permisos se comprueban en el servidor.

En la nube, PostgreSQL conserva cuentas y sesiones en tablas propias y el estado del hogar en una fila JSONB con transacciones. Las fotos se guardan en un bucket privado de Supabase. En desarrollo local se mantienen JSON y SQLite. La separación entre múltiples hogares y la normalización de compras/productos en tablas propias siguen pendientes.

## Ejecución local

Requisitos: Python 3.12, Node.js para preparar el OCR web y, para Android, Android Studio/JDK/SDK. Tesseract nativo y OpenCV son opcionales para el endpoint de escaneo local.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
npm ci
npm run build:web
Copy-Item .env.example .env
.venv/Scripts/python.exe scripts/crear_administradora.py
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Completar `.env` con la configuración de la instalación. No subir cuentas, contraseñas, tickets personales ni bases locales a GitHub. Para fotos, instalar Tesseract e indicar `TESSERACT_CMD` si no está en PATH; `TESSERACT_LANG` debe contener idiomas instalados (por ejemplo `spa+eng`).

Dashboard opcional: `python -m streamlit run web/dashboard.py`. Android: abrir el proyecto Gradle y configurar su URL HTTPS de API antes de compilar. Para acceso desde otro dispositivo consultar [seguridad](docs/SEGURIDAD.md).

## Verificación

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
Get-ChildItem frontend/web/js -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
```

Las pruebas usan datos temporales y proveedores simulados; no certifican precios en vivo ni la precisión de una fotografía concreta.

## Regresión automatizada

Ver [casos, herramientas y ejecución](docs/REGRESION.md): pytest para API, Playwright para web, Compose UI Test para Android y GitHub Actions. Las pruebas usan datos de prueba separados del hogar real.

Ver [diagnóstico del escáner, modelo OCR, formatos y ofertas](docs/ESCANER_Y_OFERTAS.md).

## Publicación y presentación

- [Módulo contable y archivo de comprobantes](docs/GASTOS_Y_COMPROBANTES.md).
- [Guía de Vercel y backend persistente](deploy/VERCEL.md).
- [Funcionalidades y tecnologías](docs/FUNCIONALIDADES.md).
- [Cuadernillo técnico de IA](CUADERNILLO_TECNICO_IA.md): material complementario; distinguir experimentos de funciones efectivamente integradas.

## Acceso al entorno de pruebas

Usuario: `test123`. Contraseña: `PruebasTest1234`. La cuenta pertenece a una demostración aislada; usar únicamente comprobantes ficticios. Versión Android: 1.1.0.
