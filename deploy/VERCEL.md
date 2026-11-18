# Publicación de Expensas House

La aplicación se publica en [expensas-house-griselda-blanco.vercel.app](https://expensas-house-griselda-blanco.vercel.app). La web y FastAPI se ejecutan en Vercel, con PostgreSQL y fotografías privadas en Supabase. No se usan rewrites a túneles de Cloudflare.

La configuración vigente está en `vercel.json` y `pyproject.toml`, en la raíz del repositorio. El proyecto Vercel debe tener esa raíz y framework FastAPI. No seleccionar `frontend/web` como directorio raíz.

La guía [Despliegue en la nube](../docs/DESPLIEGUE_NUBE.md) explica credenciales, migración, OCR, pruebas y límites gratuitos. Las actualizaciones de `main` en GitHub generan el siguiente despliegue. Verificar la API y el inicio de sesión antes de considerar exitosa una publicación.

[Documentación OpenAPI](https://expensas-house-griselda-blanco.vercel.app/docs) y [contrato JSON](https://expensas-house-griselda-blanco.vercel.app/openapi.json).
