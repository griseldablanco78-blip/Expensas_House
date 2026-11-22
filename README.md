# Expensa House

Aplicación para organizar la despensa del hogar, preparar compras, comparar ofertas y registrar gastos a partir de tickets. Tiene dos clientes: web y Android, conectados a una API Python compartida.

[Actualización: lectura de tickets, IVA y detalle de ofertas en Android](docs/ACTUALIZACION_TICKETS_OFERTAS.md).

## Documentación del proyecto

[Informe breve para la entrega](docs/INFORME_PRESENTACION.md): los seis puntos solicitados por la cátedra.

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
- **Compras y presupuesto:** resúmenes por fecha de compra en web y Android, selector mensual web, total gastado, saldo y resumen por supermercado. El presupuesto es una referencia común para el mes elegido.
- **Ofertas:** consulta ofertas guardadas; con `EXPENSA_LIVE_OFFERS=1` también consulta catálogos públicos de Día, Coto, Carrefour, Vea y Jumbo. Ratoneando permanece como proveedor opcional configurado por `RATONEANDO_API_URL`. La web permite agregar y editar ofertas reales. No hay monitoreo automático garantizado de supermercados.
- **Tickets:** tabla de productos por supermercado con detalle, precio unitario, descuento e importe neto; foto JPG/PNG/WebP o texto; OCR con Tesseract, revisión editable y confirmación del gasto con detalle. Conserva nombres en varias líneas, fecha, supermercado, texto reconocido e imagen privada de respaldo; permite descargar un archivo de lectura `.txt`. OpenCV ofrece un modo opcional para fotos con sombras. El OCR puede cometer errores y no recupera palabras ausentes en una foto cortada. Registrar el gasto no implica ingreso automático al stock.
- **Boti House:** consultas de ofertas, presupuesto y faltantes mediante reglas sobre datos del hogar. No se presenta como un modelo generativo entrenado.
- **Android y web:** comparten API; la sincronización depende de conexión y solicitudes, no de un canal de tiempo real.
- **Android 1.3.2:** usa la dirección fija de Vercel. ML Kit Text Recognition v2 con modelo latino incluido lee la foto en el teléfono; el servidor interpreta el texto y conserva el comprobante revisado. No requiere una API de IA de pago.
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

Las credenciales se comparten por un medio privado y no se publican en el repositorio. La cuenta publicada es compartida y conserva información cargada por sus usuarios. Las pruebas automatizadas que crean compras utilizan almacenamiento local separado. Versión Android: 1.3.2.

## Paquete de presentación

`python scripts/crear_zip_presentacion.py` genera `output/Presentacion_Expensas-House.zip` desde el código confirmado en Git. Incluye únicamente el código con sus archivos de configuración y recursos necesarios, y `ENLACES_PROYECTO.txt` con los enlaces a GitHub y Vercel. No contiene informes, cuadernillos, fotografías personales ni APK.

La presentación, el informe breve y la documentación de módulos se consultan en este repositorio. La APK Android 1.3.7 se distribuye por separado en [GitHub Releases](https://github.com/griseldablanco78-blip/Expensas_House/releases/tag/v1.3.7).

### Actualización 1.3.4

El detalle revisado del ticket muestra producto, cantidad, precio unitario y total. El historial Android muestra comercio, fecha e importe descontado; al tocar una compra se abre el detalle y la fotografía privada. El teclado del formulario se cierra con «Listo» y al confirmar. En Ofertas → Faltantes, los productos provienen del stock y se consultan en el comparador integrado con marca y presentación disponibles.

### Actualización 1.3.5

La oferta top identifica el menor precio entre las presentaciones que coinciden con la consulta. El descuento porcentual se muestra como información adicional y no define la recomendación top. Cada tarjeta comienza con el nombre del supermercado.

El comparador consulta los catálogos públicos de Día, Coto, Carrefour, Vea y Jumbo. Coto utiliza su búsqueda pública y toma el precio por unidad de la sucursal 200; las promociones condicionadas no se presentan como precio de una unidad. Las otras cadenas utilizan el catálogo público VTEX. La disponibilidad y los precios pueden cambiar por zona. Si una fuente falla, se conservan las demás y se informa el problema.

En Android, las ofertas se muestran en dos columnas con información ampliable. Al final de Ofertas, «Tickets guardados» lista únicamente comercio y fecha; un doble toque (o mantener presionado) abre el comprobante privado y sus productos.

La web aplica los mismos cambios de contenido: tarjetas compactas con detalle ampliable, columnas adaptadas al ancho disponible y tickets al final de Ofertas. La foto privada se abre con doble clic o doble toque; también puede abrirse con Enter al enfocar el ticket.

Cuando la consulta especifica peso o volumen, la coincidencia es estricta: «1 kg», «1000 g» y «1.000 g» son equivalentes; se excluyen 500 g, otros tamaños, presentaciones contradictorias y productos sin tamaño informado. Esta regla se aplica en la API compartida por web y Android.

### Actualización 1.3.6

Web y Android permiten eliminar un ticket desde el tachito, con confirmación. Se quita el gasto y se corrige el presupuesto; el stock no se modifica. El servidor conserva el identificador eliminado para impedir que una sincronización antigua lo restaure o se descuente dos veces al reintentar. Los enlaces a imagen y texto dejan de estar disponibles; la limpieza física de imágenes privadas sin referencia es una tarea separada de mantenimiento.

Sin peso en la consulta se admiten todos los tamaños. Con peso se exige equivalencia exacta. Se reconocen las abreviaturas de Coto «Kgm» y «Grm», de modo que «Arroz Blanco 1 kg» incluye su presentación de 1 Kgm y excluye 500 g.

Actualización del buscador: sin marca solicitada se comparan todas las marcas coincidentes de cada supermercado. Para «arroz blanco», se incluyen las descripciones de arroz simple «largo fino» y «doble carolina», aunque no contengan la palabra blanco; se excluyen integral, amarillo, arroz con azafrán u otros condimentos, parboil, arroz preparado, postres y derivados. Una marca explícita y el peso indicado siguen siendo obligatorios. La regla se ejecuta en la API utilizada tanto por web como por Android.

En arroz blanco, «doble», «fino» y «partido» solo restringen los resultados cuando la persona los escribe. Si no se especifican, se incluyen las variedades blancas coincidentes. El precio menor determina la recomendación entre las presentaciones solicitadas.

### Actualización 1.3.7

Las tarjetas de ofertas de web y Android identifican Club Día, Comunidad Coto, Mi Carrefour, Vea Ahorro y Jumbo Más según el supermercado. El detalle enlaza a la información oficial y aclara que los beneficios personales dependen de cupones, vigencia, sucursal, pago y acumulabilidad. Es un aviso informativo: no consulta cuentas de esos clubes ni calcula rebajas personales; el orden y la oferta top siguen usando el precio observado.
