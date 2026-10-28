# Cuadernillo - acceso a la actividad de Clase 10

**Estudiante:** Griselda Blanco  
**Repositorio:** Seminario2026  
**Rama:** `Proyecto_Integrador`  
**Carpeta de entrega:** `clase_10/`  
**Formato investigado:** modelo completo de PyTorch.

[Entrar a la entrega de Clase 10](https://github.com/griseldablanco78-blip/Seminario2026/tree/Proyecto_Integrador/clase_10)

[Abrir directamente el notebook](https://github.com/griseldablanco78-blip/Seminario2026/blob/Proyecto_Integrador/clase_10/Clase_10_Blanco_Griselda.ipynb)

La entrega contiene el notebook con su recorrido ejecutado y la actividad final. Las predicciones personales aún señaladas como pendientes deben completarse y revisarse antes de presentar la entrega como terminada.

---

# 📘 Cuadernillo Técnico de Inteligencia Artificial y Tecnologías - Expensa House

Este documento detalla la arquitectura de Inteligencia Artificial, los modelos preentrenados adaptados desde **Hugging Face**, las librerías, marcos de trabajo y el stack tecnológico utilizado en el desarrollo del ecosistema **Expensa House** (Aplicación Móvil Android + Servicio Web FastAPI + Dashboard Streamlit).

---

## 1. 🤖 Modelos de Inteligencia Artificial Implementados

El sistema utiliza una arquitectura **híbrida** que combina modelos de aprendizaje profundo (*Deep Learning*) preentrenados de Hugging Face y Google, junto con algoritmos de aprendizaje supervisado (*Machine Learning*) entrenados con datos locales.

---

### A. Reconocimiento de Voz a Texto (Speech-to-Text)

#### 🔬 Nombre Técnico del Modelo:
- **`facebook/wav2vec2-large-xlsr-53-spanish`** (Hugging Face Transformers)
- **Android SpeechRecognizer API / Google Speech Recognition Engine**

#### 📌 Descripción y Origen:
Modelo acústico y de lenguaje preentrenado basado en la arquitectura **Wav2Vec 2.0** de Meta AI, ajustado finamente (*fine-tuned*) para el idioma español (`es-AR`). En la aplicación móvil y el entorno web, procesa las ondas de audio capturadas por el micrófono para transformarlas en texto plano estructurado.

#### 🟢 Aporte Positivo (Beneficios para App y Web):
- **Carga de Productos Ultrarrápida**: Permite a los usuarios dictar ítems en lugar de escribirlos manualmente (ej.: *"Leche entera La Serenísima"*).
- **Inclusión y Accesibilidad**: Simplifica el uso del sistema para usuarios en movimiento o con dificultades de tipeo.
- **Normalización Fonética**: Interpreta variaciones dialectales del español rioplatense.

#### 🔴 Aspectos Negativos y Limitaciones (Trade-offs):
- **Sensibilidad al Ruido de Fondo**: Requiere cierto nivel de claridad ambiental para evitar confusiones en marcas específicas.
- **Dependencia de Red / Latencia**: En dispositivos de gama baja o conexiones lentas, la llamada al motor de reconocimiento puede experimentar un leve retraso.

---

### B. Visión por Computadora y Reconocimiento Óptico de Caracteres (OCR de Tickets)

#### 🔬 Nombre Técnico del Modelo / Librería:
- **`com.google.mlkit:text-recognition`** (Google ML Kit Vision API / Tesseract Engine)

#### 📌 Descripción y Origen:
Modelo de visión artificial basado en redes neuronales convolucionales (*CNN*) entrenado masivamente para detectar y extraer estructuras de texto en imágenes complejas como tickets, facturas y comprobantes impresos de supermercados.

#### 🟢 Aporte Positivo (Beneficios para App y Web):
- **Desmenuzamiento Automático de Tickets**: Extrae línea por línea cada producto adquirido junto con su importe individual.
- **Imputación de Categorías**: Permite clasificar automáticamente cada ítem en **Verdulería, Carnicería, Limpieza, Comestibles o Hogar**.
- **Control Presupuestario Preciso**: Suma los importes individuales y actualiza el saldo disponible sin errores de tipeo humano.

#### 🔴 Aspectos Negativos y Limitaciones (Trade-offs):
- **Calidad de la Fotografía**: Tickets arrugados, borrosos o con poca iluminación pueden dificultar la separación exacta de nombres y precios.
- **Variaciones de Formato**: Facturas de pequeños comercios sin formato estándar requieren expresiones regulares de respaldo (*Regex fallback*).

---

### C. Procesamiento de Lenguaje Natural (PLN) y Comparador de Ofertas con IA

#### 🔬 Nombre Técnico del Modelo:
- **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** / **`xlm-roberta-base`** (Hugging Face Hub)
- **Motor de Veredicto Inteligente (`web/ai_comparator.py`)**

#### 📌 Descripción y Origen:
Modelos del lenguaje basados en arquitecturas Transformer multilingües. Mapean frases y nombres de productos a un espacio vectorial de incrustaciones (*embeddings*) para calcular similitudes semánticas entre las consultas del usuario y las ofertas publicadas por los supermercados.

#### 🟢 Aporte Positivo (Beneficios para App y Web):
- **Cruce de Ofertas Complejas**: Analiza promociones del tipo *2da unidad al 70%*, *3x2* o *descuentos por tarjeta* y calcula el costo efectivo por unidad.
- **Veredictos de Compra Inteligentes**: Cruza el nivel de stock en casa con la oferta y aconseja si conviene comprar 1 unidad o realizar acopio.
- **Asistente Boti House**: Proporciona respuestas contextuales a preguntas sobre presupuesto, stock y ofertas con botones de navegación directa.

#### 🔴 Aspectos Negativos y Limitaciones (Trade-offs):
- **Estructuras de Promociones Cambiantes**: Promociones bancarias combinadas muy específicas requieren constante actualización de reglas en la base de ofertas.

---

### D. Modelo Predictivo de Reposición de Stock

#### 🔬 Nombre Técnico del Algoritmo:
- **`sklearn.ensemble.RandomForestClassifier`** (Scikit-Learn Machine Learning)

#### 📌 Descripción y Origen:
Modelo supervisado de clasificación basado en un ensamble de 100 árboles de decisión, entrenado sobre el conjunto de datos de movimientos del hogar (`data/inventario_movimientos_limpio.csv`).

#### 🟢 Aporte Positivo (Beneficios para App y Web):
- **Predicción de Agotamiento de Stock**: Identifica qué productos entrarán en estado crítico antes de que se agoten.
- **Robustez frente a Outliers**: Maneja adecuadamente picos atípicos de consumo en fechas especiales.

#### 🔴 Aspectos Negativos y Limitaciones (Trade-offs):
- **Problema de "Arrancado en Frío" (*Cold Start*)**: Requiere que un producto tenga al menos algunos registros de movimiento previos para realizar predicciones precisas.

---

## 2. 🛠️ Ficha Técnica de Tecnologías y Librerías Utilizadas

| Componente | Tecnología / Librería | Versión | Propósito Técnico |
| :--- | :--- | :--- | :--- |
| **Android UI** | Jetpack Compose (Material3) | 2024.12.01 (BOM) | Diseño declarativo reactivo de la interfaz móvil. |
| **Android Language** | Kotlin | 2.0.21 | Lenguaje principal de desarrollo móvil. |
| **Persistencia Móvil** | Room Database | 2.6.1 | Base de datos SQLite reactiva local en el teléfono. |
| **Red Móvil** | Retrofit 2 & OkHttp 4 | 2.11.0 / 4.12.0 | Cliente HTTP para sincronización REST con el servidor FastAPI. |
| **Reconocimiento Voz Android**| Android SpeechRecognizer API | Native SDK | Conversión de voz a texto en Android. |
| **OCR Móvil** | Google ML Kit Text Recognition | 16.0.0 | Extracción de texto desde imágenes de tickets. |
| **Backend API** | FastAPI + Uvicorn | 0.110+ | Servidor RESTful asíncrono para sincronización y endpoints IA. |
| **Dashboard Web** | Streamlit | 1.39+ | Panel web interactivo con controles, gráficos y voz. |
| **Visualización Web** | Plotly Express | 5.20+ | Gráficos interactivos de distribución de stock y gastos. |
| **Procesamiento Datos** | Pandas & NumPy | 2.2+ / 1.26+ | Limpieza, estructuración y manipulación de datasets. |
| **Modelos IA / PLN** | Hugging Face Transformers | 4.39+ | Modelos de lenguaje y procesamiento acústico de voz. |
| **Machine Learning** | Scikit-Learn | 1.4+ | Clasificador Random Forest para reposición de stock. |

---

## 3. 🎯 Resumen de Impacto Técnico

El ecosistema **Expensa House** logra unificar en un solo entorno móvil y web:
1. **Entrada de datos multimodal**: Tipeo manual, dictado por voz y escaneo OCR de tickets.
2. **Sincronización en espejo**: Mantiene la consistencia de inventario y finanzas en tiempo real entre el celular y la web.
3. **Toma de decisiones asistida por IA**: Sugiere compras óptimas combinando promociones reales de supermercados con las necesidades reales del hogar.
