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
    amount = r'(?<![\d.,])\$?\s*(\d[\d.,]*[.,]\d{2})(?![\d.,])'
    pending_description = []
    for line in text.splitlines():
        line = line.strip()
        norm = normalize(line)
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
        quantity = 1.0
        qty = re.match(r'^(\d+(?:[.,]\d+)?)\s*[xX]\s*', description)
        if qty:
            quantity = float(qty[1].replace(',', '.'))
            description = description[qty.end():].strip()
        description = ' '.join([*pending_description, description]).strip()
        pending_description = []
        if quantity <= 0 or not re.search(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]', description):
            continue
        line_total = money(last[1])
        if not line_total:
            continue
        unit_price = money(values[0][1]) if len(values) > 1 else cents(line_total / quantity)
        items.append({'description': description, 'quantity': quantity,
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
            'raw_text': text}


def scan_receipt(content):
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
        image = ImageOps.expand(image, border=24, fill='white')
        text = pytesseract.image_to_string(image, lang=os.getenv('TESSERACT_LANG', 'eng'),
                                          config='--psm 6 -c preserve_interword_spaces=1', timeout=40)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError('Falta instalar Tesseract OCR. También podés pegar el texto del ticket.') from exc
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('La imagen no es válida. Usá una foto JPG o PNG legible.') from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError('Tesseract no pudo leer el ticket. Revisá el idioma OCR instalado.') from exc
    except RuntimeError as exc:
        raise RuntimeError('La lectura OCR agotó el tiempo disponible. Probá recortar la foto.') from exc
    return parse_receipt(text)
