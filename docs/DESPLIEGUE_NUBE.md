# Expensas House en Vercel y Supabase

## Dirección pública

[Expensas House](https://expensas-house-griselda-blanco.vercel.app) · [OpenAPI interactivo](https://expensas-house-griselda-blanco.vercel.app/docs) · [Contrato JSON](https://expensas-house-griselda-blanco.vercel.app/openapi.json).

La web y la API FastAPI se ejecutan en Vercel. No requieren una PC encendida ni un túnel. Supabase conserva datos y comprobantes entre ejecuciones de la API. El estado compartido se recuperó desde los datos cargados manualmente en Android, conservando respaldos privados. Se mantienen planes gratuitos; no se habilitaron servicios de pago.

La cuenta del hogar es compartida: quien utilice esas credenciales podrá consultar y modificar los datos. Las pruebas que registran gastos ficticios deben ejecutarse en otro entorno, no sobre ese hogar.

## Responsabilidades

| Componente | Función |
| --- | --- |
| Frontend HTML/CSS/JavaScript | Formularios, revisión del ticket y consulta de la API. |
| FastAPI en Vercel | Autenticación, permisos, validación y reglas del hogar. |
| PostgreSQL en Supabase | Cuentas, sesiones y estado persistente del hogar. |
| Supabase Storage privado | Fotografías de comprobantes y productos. |
| Tesseract.js | OCR en el navegador con modelos LSTM español alojados junto con la web. |

OpenAPI describe los endpoints y sus datos; no es un proveedor de alojamiento ni un modelo de IA.

## Persistencia y permisos

El esquema privado `expensa` contiene siete tablas con RLS. El usuario de servidor `expensa_server` tiene acceso únicamente a las tablas de esta aplicación mediante políticas específicas; no es superusuario y no puede crear roles o bases. El navegador utiliza la sesión de Expensas House, nunca las credenciales de PostgreSQL o Storage.

Cuentas y sesiones tienen tablas independientes. El estado del hogar se conserva temporalmente como una instantánea JSONB en `app_state`. No es todavía un modelo contable completamente normalizado ni separa múltiples hogares por usuario.

`StateLock` combina un bloqueo reentrante local con una transacción y un advisory lock de PostgreSQL. Así, dos instancias de Vercel no sobrescriben simultáneamente el presupuesto. Un fallo revierte la transacción.

## Tickets

1. El navegador prepara la fotografía completa, orientada correctamente, con un máximo de 25 megapíxeles originales y una copia JPEG de hasta 3,5 MB.
2. Tesseract.js reconoce el texto en el dispositivo, sin API de IA de pago.
3. `POST /api/receipts/draft` interpreta el texto y archiva la foto privada.
4. La persona revisa supermercado, fecha, productos, cantidades, precios unitarios, descuentos y netos.
5. `POST /api/receipts/confirm` valida y registra el gasto que descuenta el presupuesto. El identificador evita duplicar un mismo ticket al reintentar.

El OCR puede cometer errores. El texto interpretado y la foto se conservan para revisión. La API local `/scan` utiliza Tesseract nativo opcional. Android 1.2.0 usa ML Kit Text Recognition v2, modelo latino incluido en la app, y envía el texto y la copia JPEG a `/draft`. Corrige la orientación EXIF, mantiene la fotografía completa y no requiere una API de IA de pago. Las versiones Android anteriores necesitan actualizarse para usar la URL fija.

## Configuración de Vercel

- Repositorio: `griseldablanco78-blip/Expensas_House`.
- Rama de producción: `main`.
- Directorio raíz: raíz del repositorio, sin `frontend/web`.
- Framework: FastAPI. Entrada: `backend.app.main:app`, declarada en `pyproject.toml`.
- Construcción: `npm ci && npm run build:web`. Los recursos web generados se publican desde `public/static`.
- Los cambios subidos a GitHub generan nuevos despliegues. Guardar variables de entorno requiere otro despliegue para aplicarlas.

Variables exclusivas del servidor: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (o la alternativa compatible `SUPABASE_SERVICE_ROLE_KEY`), `SUPABASE_STORAGE_BUCKET`, `EXPENSA_STORAGE=postgres`, `EXPENSA_AUTH_MODE=password`, `EXPENSA_PUBLIC_URL`, `EXPENSA_ALLOWED_ORIGINS` y `EXPENSA_LIVE_OFFERS=1`. En la instalación actual se utilizan `EXPENSA_DEMO_MODE=0` y `EXPENSA_SHARED_ACCOUNT=1`: se informa que la cuenta es compartida y se impide ejecutar la regresión mutante destinada a datos ficticios. Las credenciales se guardan como sensibles en Vercel y en `.env.cloud` excluido de GitHub para la migración local.

La conexión utiliza Transaction pooler, puerto 6543, TLS y consultas sin preparación persistente. La clave de Storage compatible actualmente configurada debe migrarse a una nueva clave secreta antes del retiro de las claves heredadas anunciado por Supabase.

## Migración y pruebas

`backend/migrations/001_cloud.sql` define el esquema; `002_server_access.sql` define los permisos del rol de servidor previamente provisionado. No incluyen contraseñas. `scripts/migrar_demo_nube.py` copia exclusivamente `.runtime/demo`: preserva un estado remoto existente, sube fotos referenciadas y no copia sesiones ni datos personales.

Pruebas locales: `python -m pytest -q` y `npm run test:web`. Prueba explícita de transacciones contra el entorno ficticio: establecer `EXPENSA_CLOUD_TEST=1` y ejecutar `python -m pytest tests/test_postgres_storage.py -q`. La prueba pública `npm run test:public` verifica inicio de sesión, ofertas, OCR, descuento del presupuesto y descarga de comprobantes.

## Límites del plan gratuito

Vercel no requiere un servidor local encendido. Supabase puede pausar proyectos gratuitos por baja actividad durante siete días; en ese caso se reactivan desde su panel. Esto es distinto de un túnel vencido. No se garantiza disponibilidad continua sin pausas en los planes gratuitos. Consultar la [política oficial de pausas](https://supabase.com/docs/guides/platform/free-project-pausing).
