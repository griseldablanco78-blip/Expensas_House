# Expensas House · funcionalidades y tecnologías

## Propósito

Expensas House reúne la despensa, la lista de compras, las ofertas y los gastos del hogar. Los clientes web y Android comparten una API para consultar y modificar información según los permisos de cada cuenta.

## Inventario y lista de compras

El inventario registra productos, categorías, marcas y cantidades. Distingue unidades cerradas y unidades en uso. La lista de compras organiza los pendientes de reposición. Android conserva datos locales mediante Room; el servidor mantiene el estado compartido actual en JSON.

## Comparación de ofertas

El comparador busca productos por texto o por el resultado del dictado. Considera nombre, marca y presentación, y permite ordenar por precio o descuento informado. Las ofertas guardadas se mantienen manualmente. La consulta externa depende de un proveedor configurado y de su disponibilidad; no existe una garantía de precios actualizados en todos los supermercados.

## Tickets y registro contable

El escáner recibe imágenes o texto. Pillow prepara orientación, escala y contraste; Tesseract reconoce caracteres. OpenCV ofrece un modo opcional de umbral adaptativo para fotos con sombras. El resultado es un borrador revisable con productos, cantidades, precios y total.

La confirmación registra el gasto con fecha y supermercado. La imagen de respaldo se conserva en almacenamiento privado y el texto reconocido se guarda junto con el detalle revisado. El historial permite descargar un archivo de lectura. El gasto se registra después de la revisión; no actualiza automáticamente el stock.

## Presupuesto mensual

La web permite elegir un mes, consultar sus gastos y agruparlos por supermercado. El saldo se calcula restando el gasto del mes al presupuesto de referencia configurado. Los gastos anteriores sin fecha de compra se agrupan usando su fecha de registro en horario argentino. El presupuesto de referencia es común; aún no se guarda un presupuesto histórico independiente por mes.

## Asistente Boti House

El asistente atiende consultas de ofertas, presupuesto y faltantes. La implementación usa reglas y datos disponibles del hogar; no corresponde a un modelo generativo entrenado para el proyecto. Sus respuestas pueden dirigir a la sección relacionada.

## Arquitectura y acceso

El frontend web utiliza HTML, CSS y JavaScript. Android utiliza Kotlin y Jetpack Compose. FastAPI recibe las solicitudes y comprueba sesiones y permisos. Los contratos de entrada se validan con Pydantic; las cuentas se almacenan en SQLite y las contraseñas se protegen con Argon2.

Las rutas, los servicios y la persistencia se organizan en carpetas distintas. La separación continúa de forma incremental: algunas pantallas y rutas conservan responsabilidades pendientes de extraer. La publicación permanente necesita almacenamiento persistente y una URL HTTPS estable.

## Verificación

La regresión incluye pruebas de API con pytest/TestClient, recorridos web con Playwright y pruebas Android con Compose/JUnit. Los datos sintéticos y los repositorios simulados permiten comprobar recorridos sin modificar datos reales. La precisión OCR y la cámara/galería físicas requieren además pruebas con fotografías y dispositivos reales.

Documentación relacionada: [presentación general y ejecución](Presentacion_Expensas-House.md), [guía del código](GUIA_CODIGO.md), [arquitectura](ARQUITECTURA.md) y [regresión](REGRESION.md).
