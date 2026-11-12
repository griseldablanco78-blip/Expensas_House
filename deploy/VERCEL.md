# Publicar frontend en Vercel

## Arquitectura de publicación

Esta versión conserva inventario en JSON, cuentas en SQLite y OCR en Tesseract. El backend necesita un servidor con disco persistente, HTTPS y respaldos. Publicar solo los archivos web no activa la API.

Vercel puede publicar el frontend y reenviar `/api/...` al backend mediante [rewrites a un origen externo](https://vercel.com/docs/routing/rewrites). No activar caché para respuestas de cuentas o del hogar.

## Pasos

1. Preparar el backend persistente: instalar `requirements.txt` y Tesseract; configurar `.env`, HTTPS, administradora y respaldo de `data`. Ejecutar `backend.app.main:app`.
2. Importar el repositorio en Vercel como proyecto estático, con raíz `frontend/web`, Framework Preset `Other`, comando de compilación vacío y directorio de salida `.`.
3. `frontend/web/vercel.json` ya reescribe `/static/...` a los archivos del frontend, que están en `css/` y `js/`.
4. Antes de habilitar `/api/...`, publicar el backend en un servicio con almacenamiento persistente. Vercel asigna una URL al frontend, pero eso no despliega la API Python ni hace persistentes sus archivos SQLite/JSON.
5. Cuando exista una URL HTTPS real del backend, agregar en `frontend/web/vercel.json` la reescritura `/api/:path*` hacia `https://DOMINIO-REAL/api/:path*`. El archivo `deploy/vercel.example.json` muestra el formato, pero `API_BACKEND_HOST` es solo un marcador y no debe publicarse sin reemplazarlo.
6. En el backend, usar su dominio en `EXPENSA_PUBLIC_URL`, agregar el dominio exacto de Vercel a `EXPENSA_ALLOWED_ORIGINS` y configurar `RATONEANDO_API_URL` si se quieren consultar ofertas externas. Mantener los dominios con HTTPS.
7. Publicar desde la rama revisada. Comprobar carga de `/static/js/app.js`, login, búsqueda de ofertas, guardado de productos y escaneo de ticket con detalle.
8. Agregar la URL real en README y PLAN_PROYECTO solo después de verificarla.

Las rutas absolutas `/static/...` se reescriben a los archivos de este frontend. La búsqueda web y Android usan el mismo endpoint `/api/offers/compare`; la web necesita el rewrite al backend para que las peticiones `/api/...` funcionen desde el dominio de Vercel. Verificar especialmente cookies de sesión, redirecciones de autenticación y permisos tras el proxy.

## Estado de esta entrega

El frontend tiene configuración de rutas estáticas, pero todavía no hay una URL pública verificada ni un rewrite activo a la API. Se requieren un backend persistente y su dominio HTTPS para que funcionen el login, la búsqueda de ofertas y el resto de las llamadas `/api/...`.

## Importar desde GitHub

En Vercel: **Add New → Project → Import Git Repository**, conectar GitHub y seleccionar `griseldablanco78-blip/Expensas_House`, rama `main`. Aplicar la raíz `frontend/web` y la configuración anterior. Si el repositorio no aparece, conceder a la integración acceso al repositorio. [Guía oficial](https://vercel.com/docs/git/vercel-for-github).

El módulo contable guarda imágenes en `data/receipts` y datos/texto en `data/app_state.json`. Esos archivos no están en GitHub. No desplegar la API actual con archivos locales como si fueran almacenamiento permanente de una función. Para publicar todo sin una PC encendida, falta preparar un backend persistente o migrar datos e imágenes a servicios externos. Supabase es una alternativa a evaluar para base y archivos; no se conecta automáticamente al importar GitHub.

## Actualización del 12/11/2026

El proyecto `expensas-house` utiliza framework `Other`, raíz `frontend/web`, sin compilación ni instalación de paquetes y salida `.`. `frontend/web/vercel.json` conecta la API de demostración mediante rewrite y desactiva caché de respuestas privadas. La protección adicional de Vercel se retiró con autorización explícita para publicar el entorno de pruebas; la sesión y los permisos de la aplicación permanecen activos.

La API de demostración se inicia con `scripts/iniciar_demo.py`, guarda datos ficticios en `.runtime/demo` y requiere el dominio HTTPS del túnel en `EXPENSA_PUBLIC_URL`, además del dominio frontend en `EXPENSA_ALLOWED_ORIGINS`. El túnel actual es temporal; si cambia, deben actualizarse el rewrite y la URL compilada en Android y volver a desplegar. La URL de producción funcional se registra una vez verificado el despliegue. No equivale a un backend permanente en la nube.
