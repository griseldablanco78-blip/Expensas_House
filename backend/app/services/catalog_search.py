"""Public supermarket catalog adapters. Prices come from the source, never generated."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import re
import threading
import time
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

STORES = {'Carrefour': 'https://www.carrefour.com.ar', 'Jumbo': 'https://www.jumbo.com.ar'}
_CACHE = {}
_LOCK = threading.Lock()


def catalog_offers(query):
    with _LOCK:
        cached = _CACHE.get(query)
        if cached and time.monotonic() - cached[0] < 300:
            return cached[1], cached[2]
    results, warnings = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {name: pool.submit(fetch_catalog, name, base, query) for name, base in STORES.items()}
        for name, future in futures.items():
            try:
                results.extend(future.result())
            except Exception:
                warnings.append(f'{name} no respondió o restringió la consulta. Se conservan las otras fuentes disponibles.')
    warning = ' '.join(warnings)
    with _LOCK:
        # Bound in-memory query cache; no personal household data is stored here.
        if len(_CACHE) >= 100:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[query] = (time.monotonic(), results, warning)
    return results, warning


def fetch_catalog(name, base, query):
    from backend.app.services.offers import money, normalize
    url = base + '/api/catalog_system/pub/products/search/?' + urlencode({'ft': query, '_from': 0, '_to': 19}, quote_via=quote)
    with urlopen(Request(url, headers={'Accept': 'application/json', 'User-Agent': 'ExpensaHouse/1.0'}), timeout=8) as response:
        raw = response.read(4_000_001)
    if len(raw) > 4_000_000:
        raise ValueError('Respuesta del catálogo demasiado grande')
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError('El catálogo no devolvió una lista de productos')
    result = []
    observed = datetime.now(timezone.utc).isoformat()
    for product in payload:
        if not isinstance(product, dict) or not product.get('productName'):
            continue
        for sku in product.get('items', []):
            if not isinstance(sku, dict):
                continue
            for seller in sku.get('sellers', []):
                offer = seller.get('commertialOffer') or {}
                price = money(offer.get('Price'))
                if not price or not offer.get('AvailableQuantity', 0):
                    continue
                regular = money(offer.get('ListPrice'))
                saving = f"{round((1-price/regular)*100, 2)}%" if regular and regular > price else ''
                images = sku.get('images') or []
                sku_name = str(sku.get('name') or '').strip()
                title = product['productName']
                sku_key = re.sub(r'\W+', ' ', normalize(sku_name)).strip()
                title_key = re.sub(r'\W+', ' ', normalize(title)).strip()
                if sku_key and sku_key not in title_key:
                    title = title + ' ' + sku_name
                result.append({'id': f"catalog:{name}:{sku.get('itemId', product.get('productId', ''))}",
                    'product': title, 'store': name, 'brand': product.get('brand', ''),
                    'price': price, 'saving': saving, 'image_url': images[0].get('imageUrl', '') if images else '',
                    'direct_link': product.get('link', ''), 'source': f'Catálogo web de {name}',
                    'updated_at': observed})
                break
    return result
