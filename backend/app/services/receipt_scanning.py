"""Local OCR and conservative receipt parsing. Users review before committing."""
import io
import os
import re
from decimal import Decimal, ROUND_HALF_UP

from backend.app.services.offers import normalize, money


def cents(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def parse_receipt(text):
    items, warnings = [], []
    total = None
    vat_amount = None
    vat_parts = []
    vat_summary = False
    finished = False
    amount = r'(?<![\d.,])\$?\s*(\d[\d.,]*[.,]\d{2})(?![\d.,])'
    pending_description = []
    for line in text.splitlines():
        line = line.strip()
        # OCR inserts blank lines between the name block and its price block.
        if not line:
            continue
        norm = normalize(line)
        if re.match(r'^total productos\b', norm):
            pending_description = []
            continue
        # Fiscal and payment data are never product descriptions.
        fiscal = re.search(r'\b(cuit|c\.u\.i\.t|iibb|domicilio|direccion|telefono|fecha|hora|cajero|caja|sucursal|factura|comprobante|consumidor final|inicio actividades|cae|cai|subtotal|efectivo|tarjeta|debito|credito|vuelto|cambio|pago)\b', norm)
        if re.search(r'\biva\b', norm):
            tax_values = [m for m in re.finditer(amount, line) if not line[m.end():].lstrip().startswith('%')]
            if tax_values:
                tax = money(tax_values[-1][1])
                # Prefer the explicit total over individual tax-rate rows.
                if re.search(r'total|contenido', norm):
                    vat_amount = tax
                    vat_summary = True
                elif not vat_summary:
                    vat_parts.append(tax)
                    vat_amount = cents(sum(vat_parts))
            pending_description = []
            continue
        if fiscal or re.search(r'\b(?:s\.?a\.?|s\.?r\.?l\.?)$', norm) or re.match(r'^(av[ .]|avenida |calle |ruta |codigo postal|razon social|s\.?a\.?$|s\.?r\.?l\.?$)', norm):
            pending_description = []
            continue
        quantity = 1.0
        qty = re.match(r'^(\d+(?:[.,]\d+)?)\s*[xX×]\s*', line)
        if qty:
            quantity = float(qty[1].replace(',', '.'))
            line = line[qty.end():].strip()
        values = list(re.finditer(amount, line))
        if not values:
            # Preserve wrapped names, but do not attach fiscal/header lines to products.
            if not line or re.search(r'\b(cuit|iva|fecha|hora|ticket|factura|domicilio|supermercado|cajero|subtotal|total)\b', norm):
                pending_description = []
            elif re.search(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]', line):
                pending_description.append(line)
            continue
        if re.match(r'^(?:importe\s+)?total\b', norm) and not norm.startswith('total productos'):
            pending_description = []
            total = money(values[-1][1])
            finished = True
            continue
        if finished:
            continue
        if re.match(r'^(?:descuento|bonificacion) (?:producto|articulo)\b', norm) and items:
            discount = money(values[-1][1])
            previous = items[-1]
            if discount and previous['discount'] == 0 and discount < previous['line_total']:
                previous['discount'] = discount
                previous['line_total'] = cents(previous['line_total'] - discount)
                warnings.append('Revisá el descuento asignado al producto anterior.')
            else:
                warnings.append('Descuento de producto ambiguo: revisalo manualmente.')
            pending_description = []
            continue
        if re.search(r'\b(subtotal|cuit|iva|cambio|vuelto|efectivo|tarjeta|debito|credito|pago|ahorro|descuento|bonificacion)\b', norm):
            pending_description = []
            if re.search(r'descuento|bonificacion', norm):
                warnings.append('Hay descuentos en el ticket: verificá el total final.')
            continue
        last = values[-1]
        if line[last.end():].strip(' *') not in ('', 'A', 'B', 'C'):
            continue
        description = line[:values[0].start()].strip(' $:-')
        description = ' '.join([*pending_description, description]).strip()
        pending_description = []
        if quantity <= 0 or not re.search(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]', description):
            continue
        line_total = money(last[1])
        if not line_total:
            continue
        unit_price = money(values[0][1]) if len(values) > 1 else cents(line_total / quantity)
        discount = cents(quantity * unit_price - line_total)
        if discount < 0:
            warnings.append('Revisá el precio unitario y el importe de ' + description)
            unit_price = cents(line_total / quantity)
            discount = 0
        items.append({'description': description, 'detail': '', 'discount': discount, 'quantity': quantity,
                      'unit_price': unit_price, 'line_total': line_total})
    subtotal = cents(sum(i['line_total'] for i in items))
    if total is None:
        total = subtotal
        warnings.append('No se reconoció el TOTAL impreso. Revisá el total calculado.')
    if abs(total - subtotal) > .01:
        warnings.append('El total impreso difiere de los productos reconocidos. Revisá faltantes, impuestos y descuentos.')
    if not items:
        warnings.append('No se reconocieron productos. Podés agregarlos manualmente.')
    return {'items': items, 'total': total, 'subtotal': subtotal, 'warnings': warnings,
            'raw_text': text, 'vat_amount': vat_amount, 'vat_included': True}


def scan_receipt(content, preprocessing="standard"):
    try:
        from PIL import Image, ImageOps, ImageFilter, UnidentifiedImageError
        import pytesseract
    except ImportError as exc:
        raise RuntimeError('Instalá Pillow y pytesseract desde requirements.txt para leer imágenes.') from exc
    command = os.getenv('TESSERACT_CMD')
    if command:
        pytesseract.pytesseract.tesseract_cmd = command
    elif os.path.isfile(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    try:
        image = Image.open(io.BytesIO(content))
        if image.width * image.height > 25_000_000:
            raise ValueError('La imagen supera los 25 megapíxeles.')
        image = ImageOps.grayscale(ImageOps.exif_transpose(image))
        # Keep the complete receipt: improve small print without cropping edges.
        if image.width < 1600:
            scale = min(3, 1600 / image.width, (25_000_000 / (image.width * image.height)) ** .5)
            if scale > 1:
                image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
        image = ImageOps.autocontrast(image).filter(ImageFilter.SHARPEN)
        if preprocessing == 'adaptive':
            try:
                import cv2
                import numpy as np
            except ImportError as exc:
                raise RuntimeError('Instalá requirements-ocr.txt para procesar fotos con sombras mediante OpenCV.') from exc
            pixels = np.asarray(image)
            pixels = cv2.adaptiveThreshold(pixels, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 31, 15)
            image = Image.fromarray(pixels)
        image = ImageOps.expand(image, border=24, fill='white')
        text = pytesseract.image_to_string(image, lang=os.getenv('TESSERACT_LANG', 'eng'),
                                          config='--oem 1 --psm 6 -c preserve_interword_spaces=1', timeout=40)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError('Falta instalar Tesseract OCR. También podés pegar el texto del ticket.') from exc
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('La imagen no es válida. Usá una foto JPG o PNG legible.') from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError('Tesseract no pudo leer el ticket. Revisá el idioma OCR instalado.') from exc
    except RuntimeError as exc:
        if 'timeout' in str(exc).lower():
            raise RuntimeError('La lectura OCR agotó el tiempo disponible. Probá una foto más nítida.') from exc
        raise
    result = parse_receipt(text)
    result['ocr'] = {'engine': 'Tesseract', 'model': 'LSTM', 'language': os.getenv('TESSERACT_LANG', 'eng')}
    return result
