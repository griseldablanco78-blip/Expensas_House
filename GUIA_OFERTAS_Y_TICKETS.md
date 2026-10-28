# Ofertas, chatbot y tickets

> Actualización de seguridad: seguir primero [docs/SEGURIDAD.md](docs/SEGURIDAD.md). El celular requiere HTTPS e inicio de sesión; el antiguo acceso directo HTTP por Wi-Fi queda bloqueado. Las instrucciones locales siguientes se mantienen como referencia de desarrollo.

## Iniciar la web y la API compartida

Desde PowerShell, en `C:\Users\grise\Proyectos\Proyecto_Expensa_House`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000`. Android debe apuntar a la URL HTTPS configurada mediante `expensa.apiBaseUrl` en `local.properties`. Para el emulador usar `http://10.0.2.2:8000/`. Volver a compilar si cambia esa propiedad. El APK de depuración se genera en `app/build/outputs/apk/debug/app-debug.apk`.

La vista de revisión de esta entrega se ejecutó en `http://127.0.0.1:8002`, solo accesible desde esta PC. Para el teléfono usar el servidor de puerto 8000 indicado arriba.

## Chatbot y ofertas

El mismo backend atiende Android y web:

- **1 Ofertas:** pregunta qué producto buscar. La siguiente consulta utiliza el producto escrito o dictado.
- **2 Presupuesto:** muestra presupuesto, gasto acumulado registrado y saldo disponible.
- **3 Faltantes:** informa productos con cero o una unidad cerrada.

El comparador permite ordenar por mayor descuento informado o menor precio publicado. Muestra descripción, supermercado, precio, condiciones y foto cuando la fuente dispone de ella. No inventa fotos ni precios. Sin imagen, informa “Imagen no disponible”. Una promoción sobre la segunda unidad no se interpreta como descuento sobre una sola unidad. Se muestra su porcentaje equivalente sobre el conjunto y la condición de comprar varias unidades.

Los productos deben coincidir con las palabras de la consulta, incluida la marca o presentación si se especifican. Las presentaciones diferentes no se convierten automáticamente a kilo o litro. El menor precio mostrado es el importe publicado del envase, no una garantía de menor costo por kilo/litro.

El dictado web utiliza Web Speech API cuando el navegador lo permite; Android usa el reconocedor de voz del dispositivo. Hay que autorizar el micrófono. La comprobación automatizada cubre el texto que resulta del dictado; no se grabó audio real en esta entrega.

### Ratoneando

Sitio de referencia: <https://ratoneando.ar/>. Código de la API: <https://github.com/matiasbontempo/ratoneando-go>.

La API publicada en ese repositorio recibe `GET /?q=producto` y devuelve `products` con `id`, `source`, `name`, `link`, `image`, `price`, `unit` y `unitPrice`. Ese contrato informa precios, pero no porcentajes de promoción. Por eso sus resultados no reciben descuentos inventados. El servicio alojado puede restringir el acceso desde otros sitios: se necesita una instancia propia o acceso autorizado; no se falsifica el Referer.

Antes de iniciar Uvicorn, configurar la URL de esa instancia:

```powershell
$env:RATONEANDO_API_URL = 'https://URL-DE-TU-INSTANCIA-AUTORIZADA/'
```

**No se dejó una instancia configurada ni se verificó una búsqueda externa real.** Sin esa variable o si el proveedor falla, se comparan las ofertas guardadas y se informa la limitación. El enlace “Consultar en Ratoneando” permite continuar la búsqueda en su sitio.

## Escanear tickets

Disponible en **Ofertas** de la web y **ESCANEAR TICKET** en Android. En el celular: **Ofertas → ESCANEAR TICKET → Sacar foto del ticket**. Se abre la cámara del teléfono y se captura una foto en resolución completa. Al confirmar la foto, se leen los productos y el total para revisarlos antes de **Confirmar gasto**. También se puede elegir una foto de la galería o pegar texto.

La foto se guarda temporalmente en la caché privada de la app y se comparte con la cámara mediante FileProvider. Se elimina al reconocer los productos o cerrar el formulario; si la lectura falla, **Volver a leer la foto tomada** permite reintentarlo. El teléfono debe alcanzar la API de la PC para procesar la imagen. Límite de imagen: 10 MB.

El OCR usa Tesseract local en la PC del servidor. Se instaló Tesseract y su adaptador `pytesseract` en este entorno. En otra PC:

```powershell
winget install --id UB-Mannheim.TesseractOCR --exact
```

Si está en otra ubicación, definir `TESSERACT_CMD`. El idioma predeterminado es `eng`; si se instala el paquete español, definir `TESSERACT_LANG=spa`. Las fotos no se envían a un servicio externo de OCR ni se guardan en el servidor.

Ejemplo de formato reconocido:

```text
2 x LECHE ENTERA 1500,00 3000,00
ARROZ 1200,00
TOTAL 4200,00
```

El análisis reconoce importes con decimales, descripción, cantidad explícita y total. Los diseños de ticket varían: hay que revisar y corregir los campos. No se garantiza lectura de todas las cadenas, renglones partidos, impuestos o descuentos. Si la suma de productos difiere del total, exige explicar el ajuste antes de guardar.

Confirmar conserva los productos y el total en el historial de gastos y suma el importe al gasto acumulado; el saldo se calcula como presupuesto menos gasto. Los reintentos de un mismo envío no duplican el ticket. Un envío pendiente se conserva en el navegador o teléfono para reintentarlo tras un corte de conexión.

**Se interpretó “se resta con el consumo” como descontar del presupuesto disponible.** El ticket no agrega ni descuenta stock automáticamente. El inventario mantiene su recorrido separado: abrir una unidad y terminar su consumo. Esto evita convertir compras por peso en unidades enteras o descontar dos veces una compra.

## Sincronización

Android y web comparten la API y la persistencia JSON existente. Android descarga el resultado combinado después de sincronizar. El botón de sincronización actualiza los cambios web en el teléfono; la web actualiza al recargar o pulsar 🔄. No hay actualización push.

La primera vinculación importa IDs nuevos del teléfono y conserva los datos del servidor para IDs ya compartidos. Las siguientes sincronizaciones comparan la última instantánea compartida: combinan cambios independientes y rechazan con HTTP 409 los cambios incompatibles sobre el mismo campo. El teléfono conserva sus datos ante el conflicto. No hay todavía una pantalla para resolver esos conflictos; se deben conciliar los datos antes de reintentar. Los detalles de tickets que Room no representa se conservan en el servidor y pueden consultarse desde el historial web.

La persistencia utiliza reemplazo de archivo y un bloqueo dentro del proceso. Ejecutar Uvicorn con un solo proceso; esta implementación local no proporciona bloqueo entre múltiples servidores ni autenticación para publicar en Internet.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check frontend/web/js/app.js
node --check frontend/web/js/features/receipts.js
.\gradlew.bat :app:assembleDebug --offline --console=plain
```

Se probaron las opciones del chatbot, búsqueda y ordenamiento sin datos inventados, importes argentinos, registro sin duplicados, validación de ajustes y conservación de gastos web al sincronizar Android. También se ejecutó OCR real sobre una imagen de ticket de prueba y se revisaron el formulario editable y la navegación del chatbot en el navegador. El APK compiló; falta verificar cámara, micrófono y sincronización en un teléfono real.
