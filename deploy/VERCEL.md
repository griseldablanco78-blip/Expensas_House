# Publicar frontend en Vercel

## Arquitectura de publicación

Esta versión conserva inventario en JSON, cuentas en SQLite y OCR en Tesseract. El backend necesita un servidor con disco persistente, HTTPS y respaldos. Publicar solo los archivos web no activa la API.

Vercel puede publicar el frontend y reenviar `/api/...` al backend mediante [rewrites a un origen externo](https://vercel.com/docs/routing/rewrites). No activar caché para respuestas de cuentas o del hogar.

## Pasos

1. Preparar el backend persistente: instalar `requirements.txt` y Tesseract; configurar `.env`, HTTPS, administradora y respaldo de `data`. Ejecutar `backend.app.main:app`.
2. Importar el repositorio en Vercel como proyecto estático, con raíz `frontend/web`, sin comando de compilación y salida `.`.
3. Copiar `deploy/vercel.example.json` a `frontend/web/vercel.json` y reemplazar `API_BACKEND_HOST` por el dominio HTTPS real del backend. El archivo de ejemplo no es un despliegue funcional por sí solo.
4. En el backend, usar su dominio en `EXPENSA_PUBLIC_URL` y agregar el dominio exacto de Vercel a `EXPENSA_ALLOWED_ORIGINS`. Mantener ambos con HTTPS.
5. Publicar desde la rama revisada. Comprobar carga de `/static/js/app.js`, login, búsqueda de ofertas, guardado de productos y escaneo de ticket con detalle.
6. Agregar la URL real en README y PLAN_PROYECTO solo después de verificarla.

Las rutas absolutas `/static/...` se reescriben a los archivos de este frontend. Las peticiones `/api/...` conservan un origen único desde el navegador. Verificar especialmente cookies de sesión, redirecciones de autenticación y permisos tras el proxy.

## Estado de esta entrega

No hay un proyecto Vercel vinculado en el repositorio ni una URL pública verificada. Se requieren la cuenta de despliegue y el dominio del backend persistente para completar la publicación.

## Importar desde GitHub

En Vercel: **Add New → Project → Import Git Repository**, conectar GitHub y seleccionar `griseldablanco78-blip/Expensas_House`, rama `main`. Aplicar la raíz `frontend/web` y la configuración anterior. Si el repositorio no aparece, conceder a la integración acceso al repositorio. [Guía oficial](https://vercel.com/docs/git/vercel-for-github).

El módulo contable guarda imágenes en `data/receipts` y datos/texto en `data/app_state.json`. Esos archivos no están en GitHub. No desplegar la API actual con archivos locales como si fueran almacenamiento permanente de una función. Para publicar todo sin una PC encendida, falta preparar un backend persistente o migrar datos e imágenes a servicios externos. Supabase es una alternativa a evaluar para base y archivos; no se conecta automáticamente al importar GitHub.
