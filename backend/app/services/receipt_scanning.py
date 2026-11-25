"""Local OCR and conservative receipt parsing. Users review before committing."""
import io
import os
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from backend.app.services.offers import normalize, money


def cents(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def receipt_header(text):
    """Only propose store/date from the header, never from payment or footer text."""
    header = '\n'.join(text.splitlines()[:18])
    normalized = normalize(header)
    store = ''
    for name, pattern in [('DIA', r'\bdia(?:\s+argentina)?\b'), ('Carrefour', r'\bcarrefour\b'),
                          ('Jumbo', r'\bjumbo\b'), ('Coto', r'\bcoto\b'), ('Disco', r'\bdisco\b'),
                          ('ChangoMás', r'\bchangomas\b')]:
        if re.search(pattern, normalized):
            store = name
            break
    if not store:
        for line in header.splitlines()[:5]:
            if re.search(r'\b(?:s\.?a\.?|s\.?r\.?l\.?)$', normalize(line)) and not re.search(r'cuit|iva|domicilio', normalize(line)):
                store = line.strip()[:150]
                break
    purchased = None
    found = re.search(r'\b(\d{2})[-/](\d{2})[-/](20\d{2})\b', header)
    if found:
        try:
            purchased = date(int(found[3]), int(found[2]), int(found[1])).isoformat()
        except ValueError:
            pass
    return {'store': store, 'purchase_date': purchased}


def clean_product_description(value):
    """Keep the product name and discard Coto's payment-promotion caption."""
    value = re.sub(r'\b(?:off\s+)?promo(?:cion)?\s+visa\b.*$', '', value, flags=re.I)
    value = re.sub(r'\bvisa\b.*\b(?:off\s+)?promo(?:cion)?\b.*$', '', value, flags=re.I)
    return re.sub(r'\s+', ' ', value).strip(' *-:')


def printed_receipt_total(lines, amount_pattern):
    """Find the final payable TOTAL, ignoring the separate product subtotal."""
    candidates = []
    for index, line in enumerate(lines):
        line = re.sub(r'(?<=\d)\s+([.,])\s*(?=\d{2}\b)', r'\1', line.strip())
        normalized = normalize(line)
        if re.match(r'^t[o0]tal productos\b', normalized):
            continue
        if not re.match(r'^(?:importe\s+)?t[o0]tal(?:\s+(?:a pagar|final|general|compra))?\b', normalized):
            continue
        values = list(re.finditer(amount_pattern, line))
        if not values:
            # Some OCR layouts put the bold TOTAL label and its amount on
            # separate lines. Accept only a standalone amount immediately after.
            next_lines = [re.sub(r'(?<=\d)\s+([.,])\s*(?=\d{2}\b)', r'\1', value.strip())
                          for value in lines[index + 1:index + 3] if value.strip()]
            for value in next_lines:
                if re.fullmatch(r'[$\s]*\d[\d.,]*[.,]\d{2}', value):
                    values = list(re.finditer(amount_pattern, value))
                    if values:
                        break
                else:
                    break
        if values:
            parsed = money(values[-1].group(1))
            if parsed is not None:
                candidates.append(parsed)
    return candidates[-1] if candidates else None


def printed_total_products(lines, amount_pattern):
    """Read Coto's TOTAL PRODUCTOS line separately from the final amount paid."""
    for index, source_line in enumerate(lines):
        line = re.sub(r'(?<=\d)\s+([.,])\s*(?=\d{2}\b)', r'\1', source_line.strip())
        if not re.match(r'^t[o0]tal productos\b', normalize(line)):
            continue
        values = list(re.finditer(amount_pattern, line))
        if not values:
            next_line = next((value.strip() for value in lines[index + 1:index + 3] if value.strip()), '')
            next_line = re.sub(r'(?<=\d)\s+([.,])\s*(?=\d{2}\b)', r'\1', next_line)
            if re.fullmatch(r'[$\s]*\d[\d.,]*[.,]\d{2}', next_line):
                values = list(re.finditer(amount_pattern, next_line))
        if values:
            return money(values[-1].group(1))
    return None


def parse_receipt(text):
    items, warnings = [], []
    total = None
    vat_amount = None
    vat_parts = []
    vat_summary = False
    stated_discount_total = None
    finished = False
    # A decimal followed by a measurement (2.25L, 0,50 kg) is part of the name.
    amount = r'(?<![\w.,])\$?\s*(\d[\d.,]*[.,]\d{2})(?![\d.,]|\s*(?i:ml|cl|l|lt|lts|litros?|kg|g|gr|gramos?)\b)'
    meaningful_name = lambda value: len(re.findall(r'[a-záéíóúñ]', value, re.I)) >= 2
    pending_description = []
    pending_quantity_price = None
    # Some mobile OCR engines emit the unit-price column before quantity ×.
    # Rejoin only adjacent numeric blocks; raw_text remains the original OCR.
    parsed_text = re.sub(
        r"(?m)^\s*(\d[\d.,]*[.,]\d{2})\s*\n\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*$",
        r"\2 X \1", text)
    parsed_text = re.sub(
        r"(?m)^(\s*\d+(?:[.,]\d+)?\s*[xX×])\s*\n\s*(\d[\d.,]*[.,]\d{2})\s*$",
        r"\1 \2", parsed_text)
    lines = parsed_text.splitlines()
    printed_total = printed_receipt_total(lines, amount)
    printed_products_total = printed_total_products(lines, amount)
    for line_index, line in enumerate(lines):
        line = line.strip()
        line = re.sub(r'(?<=\d)\s+([.,])\s*(?=\d{2}\b)', r'\1', line)
        # OCR inserts blank lines between the name block and its price block.
        if not line:
            continue
        norm = normalize(line)
        # Coto prints a bold item name and may place "OFF PROMO VISA" on a
        # separate row. Keep any amount on that row for the existing arithmetic,
        # but never let the card-promotion caption become part of the item name.
        visa_promotion = re.search(r'\b(?:off\s+)?promo(?:cion)?\b.*\bvisa\b|\bvisa\b.*\b(?:off\s+)?promo(?:cion)?\b', norm)
        if visa_promotion:
            promotion_amounts = list(re.finditer(amount, line))
            if not promotion_amounts:
                continue
            line = ' '.join(match.group(0) for match in promotion_amounts)
            norm = normalize(line)
        if re.match(r'^(?:cant(?:idad)?\b|descripcion\b|precio unit)', norm):
            pending_description = []
            continue
        if re.match(r'^total productos\b', norm):
            pending_description = []
            continue
        # Fiscal and payment data are never product descriptions.
        fiscal = re.search(r'\b(cuit|c\.u\.i\.t|iibb|domicilio|direccion|telefono|fecha|hora|cajero|caja|sucursal|factura|comprobante|consumidor final|inicio actividades|cae|cai|subtotal|efectivo|tarjeta|debito|credito|vuelto|cambio|pagos?)\b', norm)
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
        # This receipt layout prints quantity × unit price ABOVE the product name.
        line = re.sub(r'\(\s*(?:21[.,]00|10[.,]50|27[.,]00|0[.,]00)\s*%?\s*\)', '', line)
        quantity = 1.0
        qty = re.match(r'^(\d+(?:[.,]\d+)?)\s*[xX×]\s*', line)
        if qty:
            quantity = float(qty[1].replace(',', '.'))
            line = line[qty.end():].strip()
        values = list(re.finditer(amount, line))
        if qty and quantity > 0 and len(values) == 1 and money(values[0][1]) and not meaningful_name(line[:values[0].start()]):
            pending_quantity_price = (quantity, money(values[0][1]))
            continue
        if not values and pending_quantity_price and meaningful_name(line) and not finished:
            # A complete quantity × unit-price block can price a name-only row.
            # Keep wrapped names pending when the next row contains the net amount.
            following = next((value.strip() for value in lines[line_index + 1:] if value.strip()), '')
            boundary = not following or re.match(r'^\d{8,}$', following) or re.match(
                r'^(?:subtotal|total|descuentos?)\b', normalize(following))
            if boundary:
                count, price = pending_quantity_price
                line = f"{line} {cents(count * price):.2f}"
                values = list(re.finditer(amount, line))
                warnings.append('Se calculó el importe del producto con cantidad × precio unitario. Revisalo contra la foto.')
        if not values:
            # Preserve wrapped names, but do not attach fiscal/header lines to products.
            if not line or re.search(r'\b(cuit|iva|fecha|hora|ticket|factura|domicilio|supermercado|cajero|subtotal|total)\b', norm):
                pending_description = []
            elif meaningful_name(line):
                pending_description.append(line)
            continue
        if re.match(r'^(?:importe\s+)?total\b', norm) and not norm.startswith('total productos'):
            pending_description = []
            total = money(values[-1][1])
            pending_quantity_price = None
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
        if re.match(r'^descuentos?\s*:', norm):
            stated_discount_total = money(values[-1][1]) or 0
        if re.search(r'\b(subtotal|cuit|iva|cambio|vuelto|efectivo|tarjeta|debito|credito|pago|ahorro|descuentos?|bonificaciones?)\b', norm):
            pending_description = []
            if re.search(r'descuento|bonificacion', norm):
                warnings.append('Hay descuentos en el ticket: verificá el total final.')
            continue
        last = values[-1]
        if line[last.end():].strip(' *') not in ('', 'A', 'B', 'C'):
            continue
        description = line[:values[0].start()].strip(' $:-')
        description = clean_product_description(' '.join([*pending_description, description]))
        pending_description = []
        if quantity <= 0 or not meaningful_name(description):
            warnings.append('Se omitió una línea sin nombre de producto legible. Revisá el texto y la foto.')
            continue
        line_total = money(last[1])
        if not line_total:
            continue
        if pending_quantity_price is not None and not qty:
            quantity, unit_price = pending_quantity_price
            pending_quantity_price = None
        else:
            unit_price = money(values[0][1]) if len(values) > 1 else cents(line_total / quantity)
        discount = cents(quantity * unit_price - line_total)
        if discount < 0:
            warnings.append('Revisá el precio unitario y el importe de ' + description)
            unit_price = cents(line_total / quantity)
            discount = 0
        items.append({'description': description, 'detail': '', 'discount': discount, 'quantity': quantity,
                      'unit_price': unit_price, 'line_total': line_total})
    # Explicit zero discount + matching line totals permits arithmetic recovery of an OCR unit price.
    if stated_discount_total == 0 and total is not None and abs(sum(i['line_total'] for i in items) - total) < .02:
        for item in items:
            if item['discount'] != 0:
                item['unit_price'] = cents(item['line_total'] / item['quantity'])
                item['discount'] = 0
                warnings.append('El ticket indica descuento cero: se calculó el precio unitario a partir del neto y la cantidad. Revisalo contra la foto.')
    for item in items:
        if re.search(r'\d+[.,]\d{3}\b', item['description']):
            warnings.append('La presentación del producto puede confundir una letra con un dígito. Revisá el nombre contra la imagen.')
    subtotal = cents(sum(i['line_total'] for i in items))
    if printed_total is not None:
        total = printed_total
    if total is None:
        total = subtotal
        warnings.append('No se reconoció el TOTAL impreso. Revisá el total calculado.')
    if abs(total - subtotal) > .01:
        if printed_total is not None:
            warnings.append('Se tomó el importe del renglón TOTAL final. La diferencia con los productos reconocidos puede ser un descuento global; revisá la foto.')
        else:
            warnings.append('El total impreso difiere de los productos reconocidos. Revisá faltantes, impuestos y descuentos.')
    if not items:
        warnings.append('No se reconocieron productos. Podés agregarlos manualmente.')
    return {'items': items, 'total': total, 'subtotal': subtotal, 'warnings': warnings,
            'printed_products_total': printed_products_total, 'raw_text': text,
            'vat_amount': vat_amount, 'vat_included': True, **receipt_header(text)}


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
