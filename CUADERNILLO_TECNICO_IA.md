# Cuadernillo académico: Expensa House

**Autora:** Griselda Blanco  
**Proyecto:** Expensa House  
**Repositorio:** https://github.com/griseldablanco78-blip/Expensas_House  
**Aplicación web publicada:** https://expensas-house-griselda-blanco.vercel.app

## Datos de acceso a la demostración

- **Usuario:** `test123`
- **Contraseña:** `PruebasTest1234`
- **Versión Android:** `1.1.0`

La cuenta anterior corresponde exclusivamente al entorno ficticio de pruebas. Utilizo los datos de demostración y no información personal.

## Presentación del proyecto

Desarrollé Expensa House como una aplicación doméstica para organizar la despensa, preparar la lista de compras, comparar ofertas y registrar gastos mediante tickets. El proyecto dispone de una aplicación Android y una aplicación web que utilizan la misma API desarrollada en Python.

La web está publicada en Vercel y permite probar el sistema desde un navegador. Android guarda los datos localmente en una base Room y los sincroniza con el backend. La sincronización no es una nube automática permanente: el backend de demostración utiliza un túnel temporal y debe permanecer activo en mi computadora.

## Problema que resolví

Un hogar debe llevar diferentes controles: productos disponibles, unidades abiertas, faltantes, presupuesto, gastos y fotografías de tickets. Estos datos pueden cargarse manualmente o extraerse con diferentes herramientas. Mi objetivo fue integrar esos ingresos, mantener el estado común y permitir consultar el sistema desde dos clientes.

## Arquitectura general

```text
Android (Kotlin + Compose)
            |
            | Retrofit / HTTP / JSON
            v
Web (HTML + CSS + JavaScript) -> Vercel
            |
            v
FastAPI + servicios Python
            |
            +--> JSON: stock, compras, ofertas y gastos
            +--> SQLite: cuentas y sesiones
            +--> Archivos privados: imágenes de tickets y ofertas
            +--> Tesseract y OpenCV: lectura de comprobantes
```

Android conserva una copia local con Room/SQLite. Cuando existe conexión, solicita el estado o envía su instantánea al backend. El servidor combina los cambios con el estado central y devuelve el resultado. Si la API no responde, los datos escritos en el teléfono siguen disponibles localmente.

## Estructura de carpetas

```text
backend/app/
  main.py                 Configuración principal de FastAPI
  api/routes/             Endpoints de stock, compras, presupuesto, ofertas,
                           chatbot, voz, tickets, autenticación y sincronización
  api/schemas.py          Validación de solicitudes
  services/               OCR, tickets, ofertas, sincronización y reportes
  infrastructure/         Persistencia JSON y exportaciones compatibles
  core/                   Seguridad, autenticación y rutas

frontend/web/
  index.html              Interfaz principal
  css/                    Estilos
  js/app.js               Navegación y carga de datos
  js/core/                API y autenticación
  js/features/            Ofertas, chatbot, tickets y gastos
  vercel.json             Publicación y redirección de /api

app/src/main/
  java/com/expensahouse/app/
    data/local/           Base Room
    data/remote/          Clientes Retrofit
    data/repository/      Acceso a datos
    domain/model/         Modelos de negocio
    ui/                   Pantallas Compose y ViewModels

modelos/
  modelo_prediccion.py    Experimento de clasificación con Random Forest

data/
  app_state.json          Estado local del hogar
  receipts/               Imágenes privadas de comprobantes

tests/                    Pruebas unitarias, seguridad y Playwright
docs/                     Arquitectura y documentación técnica
deploy/                   Configuración de publicación
scripts/                  Instalación, demostración y diagnóstico
```

## Tecnologías aplicadas

| Componente | Tecnología | Uso |
|---|---|---|
| Android | Kotlin, Jetpack Compose | Interfaz móvil |
| Base local Android | Room sobre SQLite | Cache y uso sin conexión |
| Comunicación móvil | Retrofit y OkHttp | Solicitudes REST |
| Backend | Python, FastAPI y Uvicorn | API compartida |
| Web | HTML, CSS y JavaScript | Interfaz publicada |
| Publicación web | Vercel | Hospedaje estático y proxy de `/api` |
| Base central actual | JSON | Estado compartido del hogar |
| Cuentas y sesiones | SQLite | Usuarios, contraseñas y permisos |
| Contratos | Pydantic | Validación de datos |
| OCR | Tesseract, Pillow y OpenCV opcional | Lectura de tickets |
| Análisis | Pandas, NumPy y scikit-learn | Limpieza y experimento predictivo |
| Pruebas | Pytest, unittest, Playwright | API, seguridad y navegador |

## Base de datos y persistencia

Utilizo dos bases según su responsabilidad:

- **Room/SQLite en Android** conserva el inventario, compras, ofertas, presupuesto y gastos del teléfono.
- **SQLite del backend** conserva cuentas y sesiones.
- **JSON en el servidor** conserva el estado compartido actual del hogar.

Las imágenes de tickets y ofertas se guardan como archivos privados. Esta distribución permite una demostración funcional, pero todavía no es una arquitectura de producción compartida con múltiples hogares. Para una publicación permanente necesito migrar el estado central a PostgreSQL u otro servicio relacional y almacenar las imágenes en un servicio de archivos persistente.

## Sincronización web y app

Android puede enviar una instantánea completa mediante `POST /api/sync`. La base Room conserva los datos para usar la app sin conexión. Al iniciar o realizar una operación, la app intentará sincronizar con el servidor.

La web consulta stock, compras, presupuesto y gastos. Agregué una actualización automática cada quince segundos y también actualizo al volver a mostrar la pestaña del navegador. Así, los cambios enviados desde Android pueden aparecer en Vercel sin recargar manualmente la página.

El flujo actual es por solicitudes: no utiliza WebSockets ni notificaciones en tiempo real. Si el backend del túnel cambia o se corta, la web muestra un error de conexión y Android conserva sus datos locales.

## Módulos de inteligencia artificial

### 1. Voz a texto

En el navegador utilicé **Web Speech API** con idioma `es-AR`. Android utiliza el reconocedor de voz del sistema. Existe también un endpoint en FastAPI que recibe un archivo de audio y usa **SpeechRecognition** con el motor Google, pero no desarrollé ni entrené un modelo propio de voz.

Este módulo convierte el mensaje hablado en texto y lo usa para buscar productos u operar los campos admitidos. Puede equivocarse con marcas, acentos, ruido ambiental o conectividad.

### 2. Chatbot Boti House

Implementé Boti House mediante reglas de texto y datos reales del hogar. Reconoce consultas sobre ofertas, presupuesto y faltantes, calcula respuestas y abre la pestaña correspondiente.

No entrené ni integré un modelo generativo como ChatGPT. Por eso la documentación académica debe presentar esta función como un chatbot basado en reglas y no como un modelo de lenguaje entrenado.

### 3. Buscador y comparador de ofertas

El buscador normaliza el texto, elimina palabras de consulta, conserva nombre y presentación, compara ofertas guardadas y consulta proveedores externos autorizados si están configurados. También calcula el precio efectivo visible y informa cuándo una promoción corresponde a unidades múltiples.

No generó precios ni predije promociones. Los precios provienen de ofertas cargadas manualmente o de catálogos públicos. Esta función utiliza reglas y coincidencia textual; no utilizo embeddings, red neuronal ni modelo entrenado propio para el buscador.

### 4. OCR de tickets

Utilicé Tesseract con modelos `spa+eng`, Pillow para orientación y contraste y OpenCV opcional para sombras. Las expresiones y reglas permiten separar productos, cantidades, precios y descuentos.

Tesseract y los datos utilizados no fueron entrenados por mí. Corregí el resultado antes de confirmar el gasto. El OCR puede fallar con tickets arrugados, cortados o mal iluminados.

## Modelo predictivo de reposición

El archivo `modelos/modelo_prediccion.py` implementa un experimento separado con **Random Forest Classifier** de scikit-learn. Entrené sobre el CSV `inventario_movimientos_limpio.csv`, aunque ese archivo no forma parte del flujo central actual.

La predicción objetivo es:

> ¿El producto necesita reposición?

Las variables preparadas fueron categoría, frecuencia de consumo y gasto acumulado. El código calcula el stock según compras y consumos y define crítico cuando el stock calculado es menor o igual a dos.

El modelo no está integrado todavía en el inventario de producción. La app genera automáticamente la lista de faltantes según reglas simples: si el stock es menor o igual a uno. Por este motivo no presento el Random Forest como una precisión comprobada del producto hasta que haya datos históricos suficientes y se guarde el modelo entrenado.

## Predicciones y decisiones implementadas

| Función | Tipo de predicción o decisión | Estado |
|---|---|---|
| Reposición Android | Si una unidad disponible es 0 o 1, agrego el producto a faltantes | Activa |
| Random Forest | Clasifica si un producto necesita reposición | Experimento separado |
| Comparador | Ordena por precio o descuento y elige una oferta visible | Activa |
| OCR | Extrae caracteres y interpreta líneas del ticket | Activa |
| Voz | Convierte audio en texto | Activa en navegadores compatibles |
| Chatbot | Selecciona una respuesta por palabras clave y contexto | Activa |

## Acceso, seguridad y pruebas

FastAPI verifica usuario y permisos antes de devolver datos o aceptar cambios. Las contraseñas se protegen con Argon2 y las sesiones utilizan cookies HTTP-only. El modo de demostración exige datos ficticios y no debe utilizar comprobantes personales.

Probé el backend con Pytest/unittest, la interfaz web con Playwright y el cliente Android con pruebas Compose/JUnit cuando corresponde. Las pruebas usan datos temporales.

## Limitaciones académicas actuales

- El backend de demostración depende de la PC y de un túnel temporal.
- El JSON y las imágenes no son persistentes en Vercel.
- No existe aislamiento completo de hogares independientes.
- El historial predictivo todavía es insuficiente para obtener un modelo fiable.
- Los proveedores externos pueden modificar precios o denegar consultas.
- El OCR requiere revisión humana.
- La sincronización Android utiliza instantáneas y no operaciones individuales con historial completo.

## Conclusión

Con este proyecto integré una aplicación móvil, una aplicación web y un backend compartido. Incorporé carga manual, voz a texto, OCR, chatbot por reglas, comparación de ofertas y un experimento predictivo separado.

Aprendí a diferenciar funciones realmente entrenadas de modelos preentrenados, reglas locales y asistentes conversacionales. El próximo paso académico y técnico será migrar el almacenamiento central, añadir datos históricos reales de consumo y entrenamiento periódico y utilizar una infraestructura permanente.
