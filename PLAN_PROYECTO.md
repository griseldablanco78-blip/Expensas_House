# Expensa House: web, datos e inteligencia

## Diagnostico actual

La aplicacion Android guarda los datos en una base Room local llamada `expensa_db`. Las tablas actuales son:

- `stock_items`: productos, marca, categoria, unidades en stock y unidades en uso.
- `shopping_items`: lista de compras y reposicion automatica.
- `offers`: ofertas guardadas.
- `user_prefs`: presupuesto y gasto acumulado.

La base de datos del telefono no puede ser consultada directamente desde una pagina web. Para compartir los datos hay que sincronizarlos mediante una API o exportarlos a un archivo.

## Arquitectura propuesta

```text
Android Kotlin + Room
        |
        | HTTPS / JSON: sincronizacion de inventario y movimientos
        v
Python FastAPI + SQLite/PostgreSQL
        |
        +--> Streamlit: dashboard EDA, filtros e insights
        +--> modelos: reposicion, gasto y clasificacion
        +--> imagenes: catalogo y reconocimiento opcional
        +--> voz: transcripcion y comandos
```

### Fuente de datos

Para una primera demostracion se puede agregar un boton **Exportar datos** en Android que genere JSON o CSV desde Room. Para la version completa, Android enviara los cambios a FastAPI con autenticacion y un `household_id`.

El dataset para el EDA debe conservar historico. El inventario actual solo representa una fotografia. Cada cambio deberia registrar:

`fecha`, `producto`, `categoria`, `marca`, `tipo_movimiento`, `cantidad`, `precio`, `origen`.

Los movimientos pueden comenzar a registrarse desde Android. Los precios historicos se pueden cargar desde compras manuales, ofertas o un CSV publico de referencia, dejando documentada la fuente.

## MVP recomendado para la entrega

1. **Datos:** exportar el contenido actual de Room a JSON/CSV y crear una tabla historica de movimientos.
2. **API:** endpoints para importar datos, consultar stock y registrar movimientos.
3. **Web:** dashboard Streamlit con inventario, productos criticos, presupuesto, gastos y filtros por categoria.
4. **EDA:** limpieza de duplicados, categorias, faltantes, tipos numericos, fechas y valores atipicos.
5. **Visualizaciones:** stock por categoria, gasto mensual, productos de mayor reposicion, curva de Pareto y matriz de productos criticos.
6. **Modelo:** Random Forest o XGBoost para predecir si un producto necesitara reposicion en los proximos dias. La variable objetivo debe definirse a partir del historico, no de datos inventados.
7. **IA conversacional:** busqueda sobre los productos sincronizados usando texto. La respuesta debe consultar el stock real antes de responder.

## Hipotesis iniciales

Estas hipotesis deben validarse con los datos y no presentarse como conclusiones anticipadas:

1. Las categorias con mayor frecuencia de consumo concentran la mayor parte de las reposiciones.
2. Los productos con stock critico generan la mayoria de los pendientes de la lista de compras.
3. El gasto mensual aumenta cuando sube la cantidad de productos en reposicion.

## Funciones opcionales

- **Voz a texto:** en Android se puede usar `SpeechRecognizer`; en Python se puede usar Whisper para procesar audios enviados a la API.
- **Texto a voz:** Android `TextToSpeech` o una API de voz en la web.
- **Imagenes:** agregar `image_url` o una ruta de imagen al producto. Para el MVP alcanza con catalogo visual; el reconocimiento de tickets o productos queda como extension.
- **Avatar:** conviene dejarlo para el cierre visual. Puede ser un personaje 2D con estados `idle`, `listening`, `thinking` y `speaking`, sincronizados con el estado de voz. No debe ser el componente central de la evaluacion del modelo.

## Entregables

- Aplicacion Android actualizada con exportacion o sincronizacion.
- Backend Python con `requirements.txt`, variables de entorno y documentacion de endpoints.
- Dashboard Streamlit reproducible.
- Dataset bruto, dataset limpio y notebook/script de preparacion.
- Notebook o modulo de entrenamiento con metricas y justificacion del modelo.
- Documento funcional: problema, fuente de datos, limpieza, EDA, hipotesis, modelo, resultados, limitaciones y conclusiones.
- Video o guia de exposicion con el flujo Android -> API -> dashboard -> asistente.

## Orden de implementacion

La secuencia mas segura es: **exportacion Room -> dataset historico -> API -> dashboard EDA -> modelo predictivo -> voz e imagenes -> avatar**. Asi la parte evaluable funciona aunque las funciones opcionales no lleguen a completarse.
