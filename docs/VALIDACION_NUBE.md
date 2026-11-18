# Validación del despliegue en la nube

Fecha: 18 de noviembre de 2026. Entorno de demostración con datos ficticios.

## Comprobaciones

- API local: 50 casos aprobados, además de subcasos de compatibilidad y permisos.
- Web local: 7 casos aprobados; lectura real de una imagen mediante Tesseract.js, revisión de productos, descuentos y netos, guardado mensual, conservación de imagen, reintento de red y pausa/reanudación de sincronización durante OCR.
- PostgreSQL real: prueba explícita aprobada de rollback y cuatro modificaciones concurrentes mediante instancias independientes del adaptador. El marcador temporal se elimina al terminar.
- Vercel previo a producción: prueba pública completa aprobada sobre el commit `54d3071`; inicio de sesión, 37 resultados de ofertas en esa ejecución, OCR de foto ficticia, descuento por producto, registro del gasto neto y descarga autenticada de foto y texto.
- OpenAPI: `/docs` y `/openapi.json` responden correctamente; el contrato incluye `/api/receipts/draft`.
- Supabase: el asesor de seguridad no informó incidencias tras configurar políticas exclusivas del rol de servidor. No se habilitó acceso público al esquema privado.

Los resultados de ofertas dependen de los catálogos consultados y pueden variar. La primera lectura descarga el motor y el modelo español; las siguientes aprovechan la caché. La sincronización periódica se pausa durante la lectura y evita superponer consultas.

## Reproducción

```powershell
.venv/Scripts/python.exe -m pytest -q
$env:E2E_PYTHON = (Join-Path (Get-Location) '.venv/Scripts/python.exe')
npm run test:web
# Solo contra el entorno ficticio autorizado, con .env.cloud privado configurado:
$env:EXPENSA_CLOUD_TEST = '1'
.venv/Scripts/python.exe -m pytest tests/test_postgres_storage.py -q
Remove-Item Env:EXPENSA_CLOUD_TEST
npm run test:public
```

La prueba pública registra un gasto ficticio real en el entorno de demostración. No debe apuntarse a un hogar con información personal. La documentación de despliegue detalla los límites gratuitos y los pasos de reactivación de Supabase.
