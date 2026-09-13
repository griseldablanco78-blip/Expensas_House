# Expensa House

MVP Android en Kotlin + Jetpack Compose para administrar los gastos y el inventario del hogar.

## Incluye

- Presupuesto mensual con progreso de gastos.
- Inventario de mercaderia nueva y en uso.
- Alerta visual cuando queda la ultima unidad.
- Lista de compras con pendientes marcables.
- Sugerencia de compra con IA simulada para el MVP.
- Ofertas de supermercados ubicadas en Balvanera, CABA.
- Alta rapida de productos desde Inventario.

## Abrir

Abrir la carpeta en Android Studio y ejecutar la configuracion `app` en un emulador o dispositivo con Android 8.0 o superior. Android Studio descargara las dependencias de Gradle durante la sincronizacion.

## Proximo corte tecnico

1. Persistencia local con Room y movimientos de stock.
2. Notificaciones con WorkManager para reposicion.
3. API de ofertas por supermercado y geolocalizacion.
4. Servicio de IA para leer consumo historico y optimizar el presupuesto.
5. Cuenta familiar y sincronizacion segura.

## Plan web y EDA

La base Room actual es local al telefono y no puede ser leida directamente por una pagina web. La integracion propuesta es Android -> API Python -> dashboard Streamlit. El plan completo de sincronizacion, dataset historico, modelos, voz, imagenes y avatar esta en [PLAN_PROYECTO.md](PLAN_PROYECTO.md).

Para el trabajo practico se recomienda comenzar exportando los datos de Room y registrando movimientos de stock. El inventario actual sirve como estado inicial, pero no alcanza por si solo para entrenar un modelo predictivo: hace falta conservar fechas, cantidades y tipos de movimiento.
