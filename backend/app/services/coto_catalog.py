"""Read Coto's public storefront search; compare single-item prices in store 200.

Public browser search configuration is discovered from the storefront, not a
private credential. Conditional multipack/card promotions never replace the
single-item shelf price. No login or personal session is sent to the source.
"""
import json
import re
import threading
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from datetime import datetime, timezone

BASE = 'https://www.cotodigital.com.ar'
SEARCH = 'https://api.coto.com.ar/api/v1/ms-digital-sitio-bff-web/api/v1/products/search/'
_CONFIG = None
_CONFIG_LOCK = threading.Lock()


def public_bytes(url, limit):
    with urlopen(Request(url, headers={'Accept': 'application/json, text/html',
                                      'User-Agent': 'ExpensaHouse/1.0'}), timeout=8) as response:
        raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Respuesta de Coto demasiado grande')
    return raw


def search_config():
    global _CONFIG
    with _CONFIG_LOCK:
        if _CONFIG and time.monotonic() - _CONFIG[0] < 3600:
            return _CONFIG[1]
        page = public_bytes(BASE + '/', 500_000).decode('utf-8')
        script = re.search(r'src=["\'](/main\.[a-zA-Z0-9]+\.js)["\']', page)
        if not script:
            raise ValueError('Cambió el buscador público de Coto')
        code = public_bytes(BASE + script[1], 4_000_000).decode('utf-8')
        config = re.search(r'constructor:\{[^}]*apiKey:"([^"]+)"', code)
        if not config:
            raise ValueError('Configuración pública de Coto no disponible')
        _CONFIG = (time.monotonic(), config[1])
        return config[1]


def fetch_coto(query):
    params = {'key': search_config(), 'num_results_per_page': '50',
              'pre_filter_expression': json.dumps({'name': 'store_availability', 'value': '200'}), 'us': '200'}
    payload = json.loads(public_bytes(SEARCH + quote(query, safe='') + '?' + urlencode(params), 4_000_000))
    return parse_coto(payload)


def parse_coto(payload):
    from backend.app.services.offers import money
    rows = payload.get('response', {}).get('results')
    if not isinstance(rows, list):
        raise ValueError('Coto no devolvió una lista de productos')
    offers = []
    observed = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if not isinstance(row, dict):
            continue
        data = row.get('data') or {}
        if '200' not in data.get('store_availability', []):
            continue
        store_price = next((p for p in data.get('price', []) if p.get('store') == '200'), {})
        price = money(store_price.get('listPrice'))
        title = row.get('value') or data.get('sku_display_name')
        if not price or not title or not data.get('id'):
            continue
        offers.append({'id': 'catalog:Coto:' + str(data['id']), 'product': title,
                       'brand': data.get('product_brand', ''), 'store': 'Coto',
                       'price': price, 'saving': '', 'image_url': data.get('image_url', ''),
                       'direct_link': BASE + '/productos/' + quote(title.replace(' ', '-').replace('%', '') + '-', safe='') + '/' + data.get('url', '').lstrip('/'),
                       'source': 'Catálogo web de Coto · sucursal 200 · precio por unidad, sin promociones condicionadas',
                       'updated_at': observed})
    return offers
