# Presentación académica de Expensa House

**Autora:** Griselda Blanco  
**Repositorio:** https://github.com/griseldablanco78-blip/Expensas_House  
**Web:** https://expensas-house-griselda-blanco.vercel.app  
**Usuario de prueba:** `test123`  
**Contraseña de prueba:** `PruebasTest1234`

## Resumen

Desarrollé Expensa House para administrar despensa, compras, presupuesto y comprobantes desde Android y desde una web. Ambos clientes consultan una API Python compartida.

## Tecnologías

Utilicé Kotlin y Jetpack Compose en Android; Room/SQLite para datos locales; Retrofit para las llamadas HTTP; FastAPI y Python en el backend; HTML, CSS y JavaScript en la web; JSON y SQLite en el almacenamiento actual; Tesseract y Pillow para OCR; y scikit-learn para un experimento predictivo.

## Tres módulos principales de asistencia

1. **Voz a texto:** convierto el habla en texto mediante Web Speech API o el reconocedor Android. Luego utilizo el texto para buscar ofertas o completar consultas.
2. **Chatbot Boti House:** responde mediante reglas a consultas de ofertas, presupuesto y faltantes. No entrené un modelo generativo.
3. **Buscador de ofertas:** normaliza la consulta, busca coincidencias y compara precios publicados. Las ofertas pueden ser manuales o provenir de fuentes externas configuradas.

También utilizo OCR para leer tickets. El motor reconoce texto, mientras que las reglas de Python separan productos, cantidades y precios.

## Predicción

Entrené experimentalmente un Random Forest para clasificar si un producto necesita reposición. Las variables fueron categoría, frecuencia de consumo y gasto acumulado. El objetivo fue predecir stock crítico.

Todavía no incorporé ese modelo a la operación principal. Android identifica faltantes con una regla simple basada en el stock disponible.

## Datos móviles y web

Android guarda una copia en Room. Al iniciar o modificar datos, intenta sincronizar una instantánea con FastAPI. La web desplegada obtiene el estado central desde la API y actualiza sus módulos cada quince segundos.

La sincronización depende de que el backend esté disponible. El backend de demostración está temporalmente alojado en mi computadora mediante un túnel HTTPS, por lo que puede dejar de responder si apago la PC o cambia el túnel.

## Enlaces de documentación

- [Repositorio GitHub](https://github.com/griseldablanco78-blip/Expensas_House)
- [Cuadernillo técnico](../CUADERNILLO_TECNICO_IA.md)
- [Arquitectura](ARQUITECTURA.md)
- [Escáner y ofertas](ESCANER_Y_OFERTAS.md)
- [Guía de publicación](../deploy/VERCEL.md)

## Alcance y próximos pasos

La versión actual es un proyecto académico demostrable, no un sistema de producción. El próximo paso será reemplazar JSON por una base relacional persistente, guardar imágenes en almacenamiento externo y mantener un histórico suficiente para entrenar y validar modelos predictivos.
