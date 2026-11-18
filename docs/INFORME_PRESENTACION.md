# Expensas House · Presentación del trabajo

**Materia:** Técnicas de Procesamiento Digital de Imágenes

**Año y cuatrimestre:** Segundo cuatrimestre de 2026

**Nombre y apellido:** Griselda Blanco

**Docente:** Juan Ignacio Bonini

## Motivación

El proyecto surge de la necesidad de organizar productos del hogar, compras y presupuesto desde el celular y la web. La fotografía de un ticket permite transformar un comprobante impreso en productos y precios que se revisan y guardan con su fecha de compra. Al confirmar, el total pagado se registra como gasto y actualiza el presupuesto disponible. Los resúmenes permiten recordar cuánto costaba cada producto en una compra anterior.

La materia se aplica al tratamiento de la imagen y al reconocimiento de texto: se prepara una copia del ticket para OCR, se interpretan sus renglones y se conserva la foto como respaldo. Las ofertas muestran también imágenes reales de productos que llegan desde las fuentes externas junto con sus precios y condiciones, cuando están disponibles.

## Problemáticas y soluciones

- **Nombres y precios mal reconocidos:** se mejoró la preparación de imagen y la separación de renglones; cantidad y precio pueden estar encima del nombre. El texto y los importes se revisan antes de guardar. Los datos fiscales no son productos y una presentación como «2,25L» no es un precio.
- **Descuentos e IVA:** se distinguen precio unitario, descuento y neto. El IVA incluido no vuelve a sumarse: se descuenta del presupuesto el total efectivamente pagado.
- **Reintentos de conexión:** cada comprobante tiene un identificador para evitar gastos duplicados.
- **Servidor temporal:** se utilizó una URL HTTPS fija de Vercel con persistencia en Supabase, sin depender de un túnel o de una PC encendida.
- **Diferencias entre Android y web:** ambos clientes comparten la API y se incorporaron resúmenes por fecha y detalle de ofertas.

El OCR puede cometer errores; reconocer una imagen no modifica el presupuesto hasta que se revisa y confirma el gasto. La documentación técnica y la explicación de cada módulo están disponibles en GitHub.
