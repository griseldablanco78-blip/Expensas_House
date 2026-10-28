# Expensa House

Aplicación para organizar la despensa del hogar, preparar compras, comparar ofertas y registrar gastos a partir de tickets. Tiene dos clientes: web y Android, conectados a una API Python compartida.

## Enlaces

- [Repositorio](https://github.com/griseldablanco78-blip/Expensas_House)
- [Plan y estado del proyecto](PLAN_PROYECTO.md)
- URL pública: **pendiente de despliegue verificado**. La dirección local no es una URL pública.
- Desarrollo local: http://localhost:8000 · API interactiva: http://localhost:8000/docs

## Organización y responsabilidades

| Carpeta | Responsabilidad |
|---|---|
| `frontend/web/` | HTML, CSS y JavaScript del navegador. Presenta datos y llama a `/api`; no almacena secretos ni decide permisos. |
| `backend/app/api/` | Rutas HTTP y validación de los contratos de entrada. |
| `backend/app/services/` | Reglas de ofertas, lectura y registro de tickets, sincronización. |
| `backend/app/infrastructure/` | Persistencia JSON actual del hogar. |
| `backend/app/core/` | Rutas, autenticación, sesiones, permisos y protección HTTP. |
| `app/` | Cliente Android Kotlin, Compose, Room y repositorios de red. |
| `web/`, `data/db.py` | Compatibilidad con importaciones anteriores y dashboard Streamlit opcional. |
| `tests/` | Pruebas de API, permisos, cuentas y flujos. |
| `docs/`, `deploy/` | Arquitectura, exposición y guía de publicación. |

Se utiliza un monolito modular. Frontend y backend están separados en el código, aunque FastAPI puede servir ambos bajo el mismo dominio. La separación es incremental: algunas rutas aún acceden directamente a persistencia y `app.js` conserva varias pantallas. Ver [arquitectura](docs/ARQUITECTURA.md).

## Funcionalidades y límites actuales

- **Despensa:** stock, unidades en uso y lista de reposición.
- **Compras y presupuesto:** lista, gastos y saldo disponible.
- **Ofertas:** consulta ofertas guardadas y un proveedor externo si se configura `RATONEANDO_API_URL`. La web permite agregar y editar ofertas reales. No hay monitoreo automático garantizado de supermercados.
- **Tickets:** foto JPG/PNG/WebP o texto; OCR con Tesseract, revisión editable y confirmación del gasto con detalle. Conserva nombres en varias líneas. El OCR puede cometer errores y no recupera palabras ausentes en una foto cortada. Registrar el gasto no implica ingreso automático al stock.
- **Boti House:** consultas de ofertas, presupuesto y faltantes mediante reglas sobre datos del hogar. No se presenta como un modelo generativo entrenado.
- **Android y web:** comparten API; la sincronización depende de conexión y solicitudes, no de un canal de tiempo real.
- **Acceso:** por defecto usuario y contraseña (`EXPENSA_AUTH_MODE=password`). El modo de correo verificado es opcional y requiere SMTP. Los permisos se comprueban en el servidor.

Los datos del hogar se guardan en JSON y las cuentas en SQLite locales. La separación entre múltiples hogares y una base central de producción siguen pendientes.

## Ejecución local

Requisitos: Python compatible con las dependencias, Tesseract OCR para fotos y, para Android, Android Studio/JDK/SDK.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
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

## Publicación y presentación

- [Guía de Vercel y backend persistente](deploy/VERCEL.md).
- [Guion de presentación y demostración](docs/PRESENTACION.md).
- [Cuadernillo técnico de IA](CUADERNILLO_TECNICO_IA.md): material complementario; distinguir experimentos de funciones efectivamente integradas.
