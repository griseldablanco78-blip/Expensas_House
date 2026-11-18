# Cuadernillo técnico de Expensas House

- **Autora:** Griselda Blanco
- **Repositorio:** [Expensas_House](https://github.com/griseldablanco78-blip/Expensas_House)
- **Web:** [Abrir Expensas House](https://expensas-house-griselda-blanco.vercel.app)
- **API y contratos:** [OpenAPI](https://expensas-house-griselda-blanco.vercel.app/docs)
- **Versión Android verificada:** 1.3.2
- **Actualización:** 18 de noviembre de 2026.

## Enfoque de la materia: imágenes y aplicación práctica

El procesamiento de la fotografía del ticket es un eje del trabajo: adquisición completa, preparación de una copia para OCR, reconocimiento de caracteres, interpretación de productos/precios y revisión antes de registrar el gasto. El total confirmado actualiza el presupuesto y queda disponible en el resumen por fecha. No se confunde la alícuota `(21,00)` ni la presentación `2,25L` con un importe. Los catálogos externos también aportan imágenes reales de productos a las tarjetas de ofertas; estas fotos se muestran desde las URLs de la fuente, sin generación de imágenes por IA.

La [presentación principal](docs/Presentacion_Expensas-House.md) desarrolla el flujo de imágenes, la motivación, las dificultades y una tabla con la función de cada módulo. El ZIP del aula contiene solo código y TXT de enlaces; la APK de Android se descarga por separado desde GitHub Releases.

## 1. Propósito y estado del proyecto

Expensas House organiza despensa, faltantes, compras, presupuesto y comprobantes de supermercado desde Android y desde una web. Ambos clientes utilizan la misma API Python.

La web y FastAPI están publicados en Vercel. PostgreSQL y el almacenamiento privado de fotografías están en Supabase. Android mantiene una copia Room/SQLite para trabajar localmente y sincronizar cuando hay conexión. El funcionamiento publicado no depende de una PC encendida ni de un túnel.

Los registros actuales se recuperaron de los datos cargados manualmente en el teléfono. Las pruebas que agregan gastos de ejemplo se ejecutaron antes de esa recuperación; la instalación actual tiene desactivado el modo ficticio para evitar que esas pruebas vuelvan a modificar el hogar.

La cuenta publicada `test123`, contraseña `PruebasTest1234`, es compartida: quienes utilicen esas credenciales podrán consultar y modificar sus datos. La separación de hogares privados e invitaciones con permisos detallados figura como mejora futura.

## 2. Arquitectura y responsabilidades

```text
Android: Kotlin + Compose + Room + ML Kit
                  |
                  | Retrofit / HTTPS / JSON o multipart
                  v
Web: HTML + CSS + JavaScript --> FastAPI en Vercel
          |                           |
          + Tesseract.js              + cuentas, permisos y sesiones
          + Web Speech API            + reglas de ofertas y chatbot
                                      + validación contable del ticket
                                      |
                                      + PostgreSQL en Supabase
                                      + Supabase Storage privado
```

Es un monolito modular: los módulos tienen responsabilidades separadas dentro de un backend compartido. Esta estructura permite evolucionar el proyecto sin introducir la complejidad operativa de servicios independientes para cada pantalla.

| Carpeta o archivo | Responsabilidad |
| --- | --- |
| `backend/app/main.py` | Construye FastAPI y registra rutas y protecciones. |
| `backend/app/api/routes/` | Operaciones HTTP por módulo. |
| `backend/app/api/schemas.py` | Valida tipos, cantidades, importes y contratos de entrada. |
| `backend/app/services/` | Reglas de ofertas, chatbot, tickets, reportes y sincronización. |
| `backend/app/infrastructure/postgres.py` | Conexión PostgreSQL por TLS y transacciones breves. |
| `backend/app/infrastructure/state_lock.py` | Evita perder cambios entre instancias concurrentes del servidor. |
| `backend/app/infrastructure/cloud_storage.py` | Acceso del servidor a fotografías privadas. |
| `frontend/web/js/features/` | Comportamiento de cada módulo web. |
| `app/src/main/.../data/ocr/DeviceReceiptOcr.kt` | OCR del ticket en Android. |
| `app/src/main/.../data/repository/` | Coordina red, OCR y acceso a datos del cliente móvil. |
| `modelos/modelo_prediccion.py` | Experimento independiente de clasificación para reposición. |
| `tests/`, `app/src/androidTest/` | Regresión de API, web y Android. |
| `vercel.json`, `pyproject.toml` | Publicación del backend y preparación del frontend. |

En la nube, cuentas y sesiones tienen tablas propias. El estado del hogar se conserva temporalmente en una fila JSONB, con transacciones. Las fotografías están fuera de esa fila, en Storage privado. La normalización de productos, compras y movimientos en tablas relacionales propias queda pendiente.

## 3. Lenguajes, tecnologías y librerías

| Tecnología | Dónde se utiliza | Por qué se utiliza |
| --- | --- | --- |
| Python y FastAPI | Backend | Organizar endpoints, validar solicitudes y compartir reglas entre web y app. |
| Pydantic | Contratos | Rechazar datos inválidos antes de registrar operaciones. |
| PostgreSQL y psycopg | Persistencia central | Conservar datos entre ejecuciones y trabajar con transacciones. |
| Supabase Storage | Comprobantes | Separar imágenes privadas de los registros contables. |
| Argon2 | Contraseñas | Almacenar hashes de contraseña. |
| Kotlin y Jetpack Compose | Android | Construir pantallas y administrar su estado. |
| Room/SQLite | Android | Mantener una base local por cuenta. |
| Retrofit y OkHttp | Android | Llamar a la API HTTPS y adjuntar la sesión. |
| HTML, CSS y JavaScript | Web | Presentar formularios, tablas y controles del navegador. |
| Tesseract.js y WebAssembly | Web | Reconocer caracteres del ticket en el dispositivo. |
| ML Kit Text Recognition v2 | Android | OCR con el modelo latino incluido en la aplicación. |
| Pillow y ExifInterface | Imágenes | Orientar y preparar copias de las fotografías sin recortar el ticket. |
| OpenCV | OCR local opcional | Preprocesar fotografías con sombras en el flujo Python local. |
| Pandas, NumPy y scikit-learn | Experimento predictivo | Preparar datos tabulares, entrenar y evaluar clasificadores. |
| Pytest/unittest, Playwright, Compose/JUnit | Calidad | Verificar API, navegador y comportamiento Android. |
| GitHub Actions y Vercel | Publicación | Ejecutar controles y generar despliegues desde el repositorio. |

Las dependencias analíticas y el OCR nativo opcional tienen archivos de requisitos separados del backend mínimo publicado.

## 4. Qué modelos utiliza cada módulo

| Módulo | Técnica actual | Entrenamiento propio | Porcentaje de calidad disponible |
| --- | --- | --- | --- |
| Buscador de ofertas | Palabras clave, normalización de texto, marca, presentación y reglas de ordenamiento. | No requiere entrenamiento en esta versión. | No medido mediante un conjunto de consultas etiquetadas. |
| Boti House | Reglas para ofertas, presupuesto y faltantes; consulta datos del hogar. | No hay entrenamiento conversacional propio. | No hay una tasa global de aciertos publicada. |
| Voz web | Servicio de reconocimiento expuesto por Web Speech API, idioma `es-AR`. | Se utiliza el servicio disponible en el navegador. | No se midió WER con grabaciones y transcripciones de referencia. |
| Voz Android | Reconocedor instalado en el sistema mediante `RecognizerIntent`, idioma `es-AR`. | Se utiliza un servicio preexistente del dispositivo. | No se midió WER con un corpus propio. |
| OCR web | Tesseract.js 6.0.1; motor LSTM y modelo español `spa`. | Modelo preentrenado de terceros. | Pasó una regresión con ticket sintético; no hay una tasa poblacional de precisión OCR. |
| OCR Android | ML Kit Text Recognition v2 16.0.1; modelo latino incluido. | Modelo preentrenado de terceros. | Pasó una prueba de lectura completa; falta un conjunto representativo de tickets impresos. |
| Reposición experimental | `RandomForestClassifier` de scikit-learn, 100 árboles. | Existe un script de entrenamiento independiente. | No hay una evaluación reproducible vigente con el dataset disponible en esta revisión. |

**Un porcentaje de descuento es una propiedad de una oferta. Una probabilidad calculada por un clasificador describe su salida. Una métrica de evaluación mide resultados comparados con respuestas conocidas. Son valores distintos.**

## 5. Buscador de ofertas y Ratoneando

El flujo actual recibe una consulta, normaliza acentos y mayúsculas, elimina palabras de pedido y compara términos de producto, marca y presentación. Por ejemplo, transforma cantidades a unidades comparables antes de filtrar. Después ordena resultados por precio o descuento informado.

Ratoneando se considera una fuente preferida para ampliar la consulta de supermercados. Su [proyecto oficial](https://github.com/matiasbontempo/ratoneando-go) publica una API de comparación y código de conectores; no constituye un modelo entrenado por Expensas House.

El adaptador existente está en `backend/app/services/offers.py` y se configura mediante `RATONEANDO_API_URL`. El frontend público de Ratoneando utiliza `https://go.ratoneando.ar?q=...`. La consulta de servidor realizada el 18/11/2026 respondió **HTTP 403**; la integración automática con ese servicio alojado queda pendiente de disponer de acceso autorizado. El [controlador publicado](https://github.com/matiasbontempo/ratoneando-go/blob/main/controllers/normalized_scrapper.go) contiene una restricción de origen.

Mientras esa conexión no esté habilitada, Expensas House conserva ofertas manuales y conectores de catálogos públicos Carrefour/Jumbo. Cada resultado debe identificar su fuente y fecha de consulta. Los precios y promociones se toman de la fuente; no se estiman mediante un modelo.

La web incluye «Consultar en Ratoneando», que abre el sitio oficial con la misma búsqueda por palabras clave. Es una consulta externa; sus resultados no se presentan como datos importados por la API de Expensas House. La licencia del código permite estudiar o desplegar el proyecto según sus condiciones; el uso del servicio alojado requiere respetar sus controles de acceso.

**Cómo medir la calidad sin entrenar:** preparar consultas con resultados relevantes revisados, medir Precision@5, verificar equivalencia de unidades y registrar disponibilidad, antigüedad de precios y tiempo de respuesta. La regla del comparador mejora a partir de errores observados en esas consultas.

## 6. Chatbot Boti House

`POST /api/ai/chat` llama a `chat_response` en `backend/app/services/offers.py`. Sus ramas reconocen consultas de presupuesto, faltantes y ofertas. Calcula el saldo desde los gastos del mes y obtiene precios desde el comparador.

Es un asistente por reglas y contexto. El proyecto no integra entrenamiento de un modelo generativo propio. Una mejora inmediata consiste en ampliar sinónimos y aclaraciones: producto ambiguo, marca, tamaño o supermercado.

La evaluación propuesta utiliza frases con intención esperada y datos de prueba conocidos. Debe comprobar tanto la intención detectada como el importe, producto o acción devueltos. La fracción de casos aprobados describe ese conjunto de pruebas, sin garantizar aciertos en cualquier conversación.

## 7. Voz a texto

La web solicita reconocimiento a través de `SpeechRecognition` o `webkitSpeechRecognition`. Android abre el servicio instalado mediante `RecognizerIntent.ACTION_RECOGNIZE_SPEECH` y selecciona el primer texto reconocido.

Esas interfaces no identifican por sí solas la arquitectura ni la versión exacta del modelo que usa el proveedor. En el código revisado no se encontró una integración propia con Whisper ni con la librería Transformers. El soporte y el procesamiento local o remoto dependen del navegador y del servicio del dispositivo. [Referencia de Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) y [referencia Android](https://developer.android.com/reference/android/speech/RecognizerIntent).

También existe `POST /api/voice/transcribe`, que usa la librería Python SpeechRecognition y `recognize_google`. Es un flujo opcional: esa dependencia está en los requisitos analíticos y no forma parte del paquete Python mínimo de Vercel. Debe configurarse y verificarse antes de presentarlo como transcripción de servidor habilitada.

**Evaluación futura:** grabaciones autorizadas con transcripción correcta, distintas voces, marcas y niveles de ruido. WER = (sustituciones + omisiones + inserciones) / palabras de referencia. Un valor menor indica menos errores; puede superar el 100% si hay muchas inserciones. Además conviene medir cuántas consultas terminan en el producto correcto después de transcribir.

## 8. Lectura y contabilidad del ticket

La web ejecuta Tesseract.js con un modelo español; Android 1.2.0 ejecuta ML Kit con su modelo latino incluido. Ambos preparan la foto completa, respetan orientación y envían texto e imagen a `POST /api/receipts/draft`. La API interpreta las líneas mediante reglas.

El formulario permite revisar supermercado, fecha, descripción, detalle, cantidad, precio unitario, descuento y neto. `POST /api/receipts/confirm` valida importes, guarda el comprobante y registra el gasto. El identificador de la operación evita duplicar un ticket al reintentar.

La prueba Android verificó texto situado al principio y al final de la imagen y conservación de dimensiones. Esa evidencia comprueba un caso de regresión; no equivale a una precisión del 100% sobre tickets de distintos supermercados.

La evaluación pendiente debe usar tickets variados y respuestas revisadas: tasa de importes correctos, totales correctos, productos recuperados y error por caracteres. La extracción de texto y la interpretación contable se evalúan por separado. [Documentación de ML Kit](https://developers.google.com/ml-kit/vision/text-recognition/v2/android).

## 9. Experimento de reposición y métricas disponibles

`modelos/modelo_prediccion.py` prepara un Random Forest de 100 árboles, `random_state=42`, y una partición aleatoria 80% entrenamiento / 20% prueba. Las variables son categoría codificada, frecuencia de consumo y suma del campo `precio`. La etiqueta indica stock calculado menor o igual a 2.

El programa calcula accuracy y un informe de clasificación cuando dispone del CSV y de al menos diez filas agregadas. En esta revisión, ejecutar el script devolvió **«Dataset limpio no encontrado»**: falta `data/inventario_movimientos_limpio.csv`. No se produjo un entrenamiento nuevo, un modelo guardado ni un porcentaje de evaluación verificable.

Hay decisiones pendientes antes de usarlo para pronosticar:

- Agrupar movimientos por producto/categoría produce una fila por grupo. Miles de movimientos no equivalen a miles de ejemplos independientes.
- La etiqueta actual describe stock acumulado; para predecir faltantes futuros debe definirse un horizonte, por ejemplo siete días.
- Los datos de entrada deben estar disponibles antes de ese horizonte. Utilizar información posterior introduciría fuga de datos.
- La regla activa de faltantes utiliza stock menor o igual a 1; el experimento utiliza menor o igual a 2. Debe acordarse un criterio de negocio.
- Debe definirse si `precio` significa precio unitario o importe del movimiento; sumar ambos conceptos indistintamente altera las variables.

Este experimento no decide actualmente el stock ni los gastos de la aplicación.

## 10. Cómo mejorar futuras predicciones sin pagar servicios

Más datos útiles pueden ayudar, pero la calidad depende también de representatividad, etiquetas correctas, variación y evaluación. Duplicar filas o mezclar información futura puede elevar un porcentaje aparente sin mejorar las predicciones reales.

| Dato a registrar | Utilidad |
| --- | --- |
| Fecha/hora, producto e identificador de hogar autorizado | Reconstruir la secuencia de consumo. |
| Tipo de movimiento y cantidad en una unidad consistente | Separar compras, consumos, ajustes y descartes. |
| Stock antes/después y unidades abiertas | Medir disponibilidad real. |
| Fecha de reposición y cantidad comprada | Evaluar ciclos de compra. |
| Precio unitario, descuento, tienda y fecha | Comparar precios observados correctamente. |
| Faltante real dentro del horizonte elegido | Construir una etiqueta comprobable. |

**Secuencia propuesta:**

1. Mantener la regla actual como referencia y definir el objetivo concreto.
2. Reunir historial autorizado, corregir duplicados y reservar periodos posteriores para prueba.
3. Comparar una referencia simple, Logistic Regression y Random Forest. Usar validación temporal si se predicen eventos futuros.
4. Medir recall de faltantes, precision de alertas, F1, balanced accuracy y matriz de confusión; informar tamaño y distribución de clases.
5. Elegir según utilidad, errores, tiempo y costo de ejecución. Guardar la versión, fecha de corte y evaluación.
6. Probar la recomendación con revisión humana antes de automatizar compras.

Si 90 de 100 ejemplos fueran «sin faltante», responder siempre «sin faltante» daría 90% de accuracy y detectaría cero faltantes. Es un ejemplo ilustrativo, no un resultado de Expensas House.

No existe una cantidad universal de filas que garantice 90% o 95%. Las curvas de aprendizaje permiten observar si agregar ejemplos mejora la validación. Para un hogar con poco historial, las reglas y el consumo promedio son referencias razonables antes de modelos más complejos. El entrenamiento tabular puede realizarse localmente con scikit-learn, sin contratar una API.

Referencias: [fuga de datos y pipelines](https://scikit-learn.org/stable/common_pitfalls.html), [validación temporal](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), [clasificador de referencia](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html), [balanced accuracy](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html) y [curvas de aprendizaje](https://scikit-learn.org/stable/modules/learning_curve.html).

## 11. APIs utilizadas y motivo de elección

| Interfaz | Función en Expensas House | Motivo y estado |
| --- | --- | --- |
| FastAPI `/api/stock`, `/shopping`, `/sync` | Inventario y sincronización. | Compartir las mismas reglas entre clientes. |
| `/api/receipts/draft` y `/confirm` | Interpretar y registrar un ticket revisado. | Separar lectura, revisión y confirmación contable. |
| `/api/offers/compare` | Comparar ofertas. | Unificar consultas escritas, dictadas y del chatbot. |
| `/api/ai/chat` | Resolver consultas por reglas. | Reutilizar stock, presupuesto y comparador. |
| Catálogos públicos Carrefour/Jumbo | Obtener precios observados. | Conectores actualmente disponibles; pueden cambiar o restringir acceso. |
| Ratoneando | Fuente preferida de comparación ampliada. | Adaptador preparado; servicio alojado respondió 403 en la revisión. |
| Web Speech API y RecognizerIntent | Voz a texto. | Aprovechar reconocimiento existente, sin entrenamiento propio. |
| ML Kit y Tesseract.js | OCR. | Reconocimiento en el dispositivo, con modelos preentrenados. |
| Supabase PostgreSQL/Storage | Datos e imágenes persistentes. | Separar almacenamiento de las ejecuciones de Vercel. |
| OpenAPI `/docs` y `/openapi.json` | Describir contratos. | Facilitar comprensión y pruebas de integración. |

PostgreSQL se conecta mediante psycopg/TLS; no es una API HTTP de IA. OpenAPI documenta la API de la aplicación. No hay una integración de pago con OpenAI en este proyecto.

## 12. Mejoras futuras: hogares y colaboración

**Estado: propuesta, no implementada como aislamiento completo de hogares.** Actualmente existen cuentas y perfiles básicos sobre un hogar compartido. Crear otra cuenta no crea automáticamente un hogar privado independiente.

El objetivo es que cada persona tenga credenciales propias y participe únicamente en los hogares a los que fue invitada. La administradora decide qué módulos y datos comparte.

| Perfil propuesto | Acceso |
| --- | --- |
| Administradora del hogar | Invitar/revocar miembros, asignar permisos, configurar presupuesto y consultar historial. |
| Familiar que compra | Agregar productos, asumir una compra, marcarla como realizada y registrar el comprobante permitido. |
| Familiar que administra stock | Registrar ingresos, consumos y ajustes; resolver faltantes. |
| Colaborador limitado o amiga | Consultar y editar la lista autorizada, sin acceder automáticamente a gastos o presupuesto. |
| Consulta | Leer únicamente los módulos autorizados. |

Ejemplo de colaboración: una persona agrega leche a la lista; otra indica «me encargo»; al comprarla confirma cantidad y comprobante. La operación actualiza stock y resuelve el faltante una sola vez. Marcar «comprado» conserva el historial y evita perder información por borrar directamente la fila.

La implementación futura requiere hogares identificados, membresías, invitaciones con vencimiento, permisos comprobados en cada solicitud y registros asociados al hogar. El historial debe indicar quién agregó, compró, consumió o corrigió un producto. Las invitaciones se pueden revocar y los cambios accidentales deben poder restaurarse. [Referencia de autorización OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

## 13. Recomendaciones para una versión comercial y profesional

Las siguientes mejoras están ordenadas por valor para un producto colaborativo, sin activar servicios de pago.

| Prioridad | Mejora propuesta | Resultado esperado y criterio de revisión |
| --- | --- | --- |
| Primera | Hogares privados, invitaciones y permisos por módulo | Un miembro no puede consultar otro hogar ni un módulo que no comparte. |
| Primera | Compra asignada, estados y confirmación idempotente | Dos personas no descuentan presupuesto ni suman stock dos veces por la misma compra. |
| Primera | Historial y recuperación de cambios | Identificar autor, fecha y motivo; restaurar un ajuste equivocado. |
| Primera | Respaldo/restauración, seguimiento de errores y estado del servicio | Recuperar datos y detectar fallos antes de que dependan del aviso del usuario. |
| Siguiente | Comprobantes y reportes mensuales claros | Filtrar por mes, tienda, categoría y persona autorizada; exportar información revisada. |
| Siguiente | Precios históricos por unidad y fuente | Comparar el mismo tamaño y fecha; distinguir precio pagado de oferta publicada. |
| Siguiente | Incorporación inicial y diseño accesible | Entender el primer uso, usar teclado/lector de pantalla y reconocer errores de formulario. |
| Siguiente | Web instalable PWA | Acceso desde la pantalla de inicio y actualización web centralizada. El modo sin conexión requiere trabajo adicional. |
| Posterior | Avisos de reposición y vencimientos configurables | Recordatorios elegidos por el usuario, con control de frecuencia. |
| Posterior | Lectura de códigos de barras y productos habituales | Reducir escritura sin reemplazar la confirmación del producto y la presentación. |
| Posterior | Predicción de consumo con historial validado | Recomendar reposición con una métrica documentada y posibilidad de corregirla. |

Para la presentación profesional conviene una portada con el problema que resuelve, capturas demostrativas, funciones disponibles, límites claros y una experiencia inicial breve. Las capturas públicas deben utilizar datos de ejemplo separados del hogar real.

Como referencias de implementación se proponen [WCAG para accesibilidad](https://www.w3.org/WAI/standards-guidelines/wcag/) y los [requisitos de una PWA instalable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).

La infraestructura gratuita sirve para validar el producto y sus límites. Supabase puede pausar proyectos gratuitos por baja actividad; no corresponde prometer disponibilidad comercial garantizada bajo esa condición. Se conserva el requisito de costo cero y no se activa una mejora de plan.

## 14. Calidad y trazabilidad

Se verificaron 50 pruebas locales de API, siete escenarios web, una prueba explícita de transacciones PostgreSQL y tres comprobaciones Android en el teléfono: OCR real sobre una imagen sintética completa, reintento y conexión de solo lectura a la nube. La prueba pública de ticket se realizó con datos ficticios antes de recuperar los registros manuales.

**Esos resultados son pruebas funcionales, no porcentajes de precisión de un modelo predictivo.** El proyecto debe informar por separado pruebas aprobadas, métricas de modelos y condiciones de evaluación.

[Validación del despliegue](docs/VALIDACION_NUBE.md) · [Guía del código](docs/GUIA_CODIGO.md) · [Despliegue y límites](docs/DESPLIEGUE_NUBE.md).
