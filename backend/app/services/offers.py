"""Offer search shared by voice, text, chat and Android. Never invent prices."""
import json
import math
import os
import re
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.app.infrastructure.json_store import get_offers, get_stock, get_user_prefs


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value or ''))
                   if not unicodedata.combining(c)).lower()


def clean_query(value):
    text = normalize(value)
    # Compare quantities in a common unit, including compact names such as 1L.
    text = re.sub(r'\b(?:un|una)\s+(?=litros?\b|kilos?\b)', '1 ', text)
    def quantity(match):
        amount = float(match[1].replace(',', '.'))
        unit = match[2]
        volume = unit in {'l', 'lt', 'lts', 'litro', 'litros', 'ml', 'cc', 'mililitro', 'mililitros'}
        base = amount * (1000 if unit in {'l', 'lt', 'lts', 'litro', 'litros', 'kg', 'kilo', 'kilos', 'kilogramo', 'kilogramos'} else 1)
        return f" {base:g}{'ml' if volume else 'g'} "
    text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*(mililitros?|kilogramos?|litros?|kilos?|gramos?|lts?|ml|cc|kg|g|l)\b', quantity, text)
    # Remove complete command words, never substrings of a product name.
    noise = {'quiero', 'quisiera', 'saber', 'consulta', 'consultar', 'buscar', 'busca',
             'buscame', 'mostrame', 'mostrar', 'dame', 'traeme', 'comparar', 'compara',
             'oferta', 'ofertas', 'precio', 'precios', 'descuento', 'descuentos',
             'mayor', 'mejor', 'mejores', 'mas', 'barato', 'barata', 'economico',
             'economica', 'top', 'donde', 'esta', 'estan', 'cuanto', 'cuesta', 'sale',
             'producto', 'productos', 'supermercado', 'supermercados', 'en', 'de',
             'del', 'el', 'la', 'los', 'las', 'un', 'una', 'por', 'para', 'que', 'hay',
             'tiene', 'tienen', 'con', 'favor', 'me', 'cual', 'es'}
    return ' '.join(w for w in re.findall(r'\d+(?:\.\d+)?(?:ml|g)\b|[a-z0-9]+', text) if w not in noise)


def money(value):
    if isinstance(value, (float, int)):
        number = float(value)
    else:
        text = re.sub(r'[^0-9,.-]', '', str(value or ''))
        if ',' in text and '.' in text and text.rfind('.') > text.rfind(','):
            text = text.replace(',', '')
        elif ',' in text:
            text = text.replace('.', '').replace(',', '.')
        elif re.fullmatch(r'\d{1,3}(?:\.\d{3})+', text):
            text = text.replace('.', '')
        try:
            number = float(text)
        except ValueError:
            return None
    return number if math.isfinite(number) and number > 0 else None


def ratoneando_offers(query):
    """Use a configured, authorized instance of the public ratoneando-go API.

    The public hosted service can restrict callers. Do not spoof its Referer.
    Contract: https://github.com/matiasbontempo/ratoneando-go
    """
    base = os.getenv('RATONEANDO_API_URL', '').strip()
    if not base:
        return [], 'Ratoneando no está configurado. Se muestran solo las ofertas guardadas.'
    url = base + ('&' if '?' in base else '?') + urlencode({'q': query})
    try:
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=12) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or not isinstance(payload.get('products'), list):
            raise ValueError('Formato de respuesta inesperado')
        results = []
        for item in payload['products']:
            if not isinstance(item, dict):
                continue
            price = money(item.get('price'))
            if not price or not item.get('name') or not item.get('source'):
                continue
            results.append({'id': 'ratoneando:' + str(item.get('id', len(results))),
                            'product': item['name'], 'store': item['source'],
                            'price': price, 'image_url': item.get('image', ''),
                            'direct_link': item.get('link', ''), 'source': 'Ratoneando',
                            'updated_at': payload.get('timestamp'),
                            'unit_price': money(item.get('unitPrice')), 'unit': item.get('unit', ''),
                            'saving': ''})
        warning = 'Algunos supermercados no respondieron.' if payload.get('failedScrapers') else ''
        return results, warning
    except Exception:
        return [], 'Ratoneando no respondió. Se muestran solo las ofertas guardadas.'


def compare_supermarket_offers(raw_query, sort='discount'):
    query = clean_query(raw_query)
    tokens = set(query.split())
    remote, warning = ratoneando_offers(query) if query else ([], '')
    offers = []
    missing_prices = 0
    sizes = {t for t in tokens if re.fullmatch(r'\d+(?:\.\d+)?(?:ml|g)', t)}
    names = tokens - sizes
    for item in [*get_offers(), *remote] if query else []:
        product = str(item.get('product') or '')
        words = set(clean_query(product + ' ' + str(item.get('brand') or '')).split())
        # Unknown size is visible as a candidate, never asserted as equivalent.
        product_sizes = {t for t in words if re.fullmatch(r'\d+(?:\.\d+)?(?:ml|g)', t)}
        if not names.issubset(words) or (sizes and product_sizes and not sizes.issubset(product_sizes)):
            continue
        size_unknown = bool(sizes and not product_sizes)
        price = money(item.get('price'))
        if not price:
            missing_prices += 1
            continue
        promo = str(item.get('saving') or '')
        # A second-unit discount is NOT a discount on a single unit.
        bulk = bool(re.search(r'2\s*(?:do|da|°|a)|segunda|3\s*x\s*2', normalize(promo)))
        pct = re.search(r'(\d+(?:[.,]\d+)?)\s*%', promo)
        discount = min(100, float(pct[1].replace(',', '.'))) if pct else 0
        if bulk:
            discount = discount / 2 if pct else (100 / 3 if re.search(r'3\s*x\s*2', promo) else 0)
        offers.append({'id': item.get('id', ''), 'product': product,
                       'store': item.get('store', 'Supermercado'), 'store_badge': '',
                       'brand': item.get('brand', 'Sin marca informada'),
                       'promo_price': price, 'regular_price': price,
                       'unit_effective_price': price, 'saving_percent': round(discount, 2),
                       'promo_text': promo or 'Sin descuento informado',
                       'promo_type': 'bulk' if bulk else 'direct',
                       'conditions': ' '.join(filter(None, [
                           'Requiere comprar varias unidades. Revisá condiciones.' if bulk else '',
                           'Presentación sin confirmar: la fuente no informa el tamaño solicitado.' if size_unknown else ''])),
                       'size_confirmed': not size_unknown,
                       'image_url': item.get('image_url') or item.get('imageUrl') or '',
                       'direct_link': item.get('direct_link', ''),
                       'source': item.get('source', 'Oferta guardada'),
                       'updated_at': item.get('updated_at'), 'unit': item.get('unit', ''),
                       'unit_price': money(item.get('unit_price'))})
    offers.sort(key=(lambda o: (not o['size_confirmed'], o['promo_price'], -o['saving_percent'])) if sort == 'price'
                else (lambda o: (not o['size_confirmed'], -o['saving_percent'], o['promo_price'])))
    confirmed = [o for o in offers if o['size_confirmed']]
    best = min(confirmed or offers, key=lambda o: o['promo_price']) if offers else None
    top = offers[0] if offers else None
    if missing_prices:
        warning = ' '.join(filter(None, [warning,
            f'{missing_prices} oferta(s) coincide(n), pero no tienen un precio válido. Completá el precio en las ofertas guardadas para poder compararlas.']))
    if any(not o['size_confirmed'] for o in offers):
        warning = ' '.join(filter(None, [warning, 'Hay coincidencias sin tamaño informado; confirmá la presentación antes de comparar precios.']))
    stock = next((s for s in get_stock() if tokens and tokens.issubset(
        set(clean_query(s.get('name', '') + ' ' + s.get('brand', '')).split()))), None)
    verdict = (f"Oferta top: {top['product']} en {top['store']}, ${top['promo_price']:,.2f}. "
               f"{top['promo_text']}. Menor precio publicado: {best['store']} (${best['promo_price']:,.2f}). "
               'Las presentaciones pueden variar; revisá tamaño, vigencia y condiciones antes de comprar.'
               if top else 'No se encontraron ofertas coincidentes con precio. Probá con el nombre y la marca del producto.')
    if top and not top['size_confirmed']:
        verdict = 'Coincidencia orientativa: la presentación solicitada no está confirmada. ' + verdict
    if not top and missing_prices:
        verdict = 'Se encontró el producto, pero falta un precio válido en la oferta guardada. Completá el precio y la presentación para poder compararlo.'
    return {'query': raw_query, 'cleaned_query': query, 'product_name': top['product'] if top else query,
            'category': stock.get('category', 'Comestibles') if stock else 'Comestibles',
            'offers': offers, 'top_offer': top, 'sort': sort, 'warning': warning,
            'external_search_url': 'https://ratoneando.ar/?' + urlencode({'q': query}),
            'ai_analysis': {'best_single': {'store': best['store'] if best else '',
                                          'price': best['promo_price'] if best else 0},
                            'best_bulk': {'store': '', 'effective_price': 0},
                            'max_saving_percent': max((o['saving_percent'] for o in offers), default=0),
                            'verdict': verdict,
                            'stock_alert': f"En casa: {stock['stockQuantity']} cerradas y {stock.get('inUseCount', 0)} abiertas." if stock else None}}


def chat_response(message, context=None):
    text = normalize(message).strip()
    selection = re.fullmatch(r'(?:opcion\s*)?([123])(?:[. ·-].*)?', text)
    option = selection[1] if selection else None
    if text in {'hola', 'buenas', 'ayuda', 'menu', 'buen dia', 'buenos dias'}:
        return {'answer': 'Elegí: 1 Ofertas · 2 Presupuesto · 3 Faltantes.'}
    if option == '2' or re.search(r'\b(presupuesto|saldo|gaste|gastado|gastos|plata|dinero)\b', text):
        prefs = get_user_prefs()
        budget, spent = prefs.get('monthlyBudget', 0), prefs.get('totalSpent', 0)
        return {'answer': f"Presupuesto: ${budget:,.2f}\nGastado: ${spent:,.2f}\nDisponible: ${budget-spent:,.2f}", 'action': 'budget'}
    if option == '3' or re.search(r'\b(faltantes|falta|faltan|stock|reponer|reposicion|terminando)\b', text):
        critical = [s for s in get_stock() if s.get('stockQuantity', 0) <= 1]
        answer = '\n'.join(f"• {s['name']}: {s.get('stockQuantity', 0)} cerradas" for s in critical)
        return {'answer': answer or 'Tu inventario no tiene productos con stock crítico.', 'action': 'stock'}
    if option == '1':
        return {'answer': '¿Qué producto querés comparar? Escribí o dictá su nombre y, si querés, la marca.', 'context': 'offers', 'action': 'comparator'}
    if context == 'offers' or re.search(r'\b(oferta|ofertas|barato|barata|precio|descuento|comparar)\b', text) or clean_query(message):
        comparison = compare_supermarket_offers(message, 'price' if 'barat' in text else 'discount')
        return {'answer': comparison['ai_analysis']['verdict'], 'comparison': comparison,
                'action': 'comparator', 'context': 'offers'}
    return {'answer': 'Elegí: 1 Ofertas · 2 Presupuesto · 3 Faltantes.'}


def answer_ai_chat_query(message):
    return chat_response(message)['answer']
