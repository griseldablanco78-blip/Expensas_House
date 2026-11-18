# Presentación académica de Expensa House

**Autora:** Griselda Blanco  
**Repositorio:** https://github.com/griseldablanco78-blip/Expensas_House  
**Web:** https://expensas-house-griselda-blanco.vercel.app  
**Usuario de prueba:** `test123`  
**Contraseña de prueba:** `PruebasTest1234`

## Resumen

Desarrollé Expensa House para administrar despensa, compras, presupuesto y comprobantes desde Android y desde una web. Ambos clientes consultan una API Python compartida.

## Tecnologías

El proyecto utiliza Kotlin y Jetpack Compose en Android; Room/SQLite para la copia local; Retrofit para llamadas HTTP; FastAPI y Python en Vercel; HTML, CSS y JavaScript en la web; PostgreSQL y Storage privado de Supabase para persistencia; Tesseract.js y modelos LSTM español para OCR en el navegador; y scikit-learn para un experimento predictivo. El desarrollo local conserva adaptadores JSON y SQLite.

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

La web y la API están alojadas en Vercel y guardan datos en Supabase. No dependen de una computadora encendida ni de un túnel. La sincronización requiere conexión. El plan gratuito de Supabase puede pausar el proyecto por baja actividad y permite reactivarlo desde el panel.

## Enlaces de documentación

- [Repositorio GitHub](https://github.com/griseldablanco78-blip/Expensas_House)
- [Cuadernillo técnico](../CUADERNILLO_TECNICO_IA.md)
- [Arquitectura](ARQUITECTURA.md)
- [Escáner y ofertas](ESCANER_Y_OFERTAS.md)
- [Guía de publicación](../deploy/VERCEL.md)

## Alcance y próximos pasos

La versión actual es un proyecto académico de demostración con datos ficticios y almacenamiento persistente en la nube. Las cuentas y sesiones tienen tablas propias; el estado del hogar usa temporalmente una fila JSONB. Quedan pendientes la normalización de compras/productos en tablas independientes, la separación de hogares, la adaptación del escáner Android al flujo de OCR del dispositivo y un histórico suficiente para validar modelos predictivos. Ver [despliegue y límites](DESPLIEGUE_NUBE.md).
