"""Lightweight visual matching for user photos and public catalog product images."""
from concurrent.futures import ThreadPoolExecutor
import base64
from functools import lru_cache
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 2_000_000
MAX_PIXELS = 16_000_000
ALLOWED_IMAGE_HOSTS = (
    'supermercadosdia.com.ar', 'cotodigital.com.ar', 'cotodigital3.com.ar',
    'carrefour.com.ar', 'vea.com.ar', 'jumbo.com.ar', 'vtexassets.com', 'vteximg.com.br',
)


def _decode(raw):
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.width * source.height > MAX_PIXELS:
                return None
            return ImageOps.exif_transpose(source).convert('RGB')
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _allowed_catalog_url(url):
    parsed = urlparse(str(url or ''))
    host = (parsed.hostname or '').lower()
    return parsed.scheme == 'https' and any(host == suffix or host.endswith('.' + suffix)
                                             for suffix in ALLOWED_IMAGE_HOSTS)


@lru_cache(maxsize=64)
def _remote_image_bytes(url):
    if not _allowed_catalog_url(url):
        return None
    try:
        request = Request(url, headers={'Accept': 'image/webp,image/png,image/jpeg',
                                        'User-Agent': 'ExpensaHouse/1.0'})
        with urlopen(request, timeout=3) as response:
            # Follow catalog CDN redirects only when they stay on an approved image host.
            if not _allowed_catalog_url(response.geturl()):
                return None
            raw = response.read(MAX_IMAGE_BYTES + 1)
        if len(raw) > MAX_IMAGE_BYTES or not _decode(raw):
            return None
        return raw
    except Exception:
        return None


def _trim_white(image):
    """Trim catalog white margins while keeping bright product areas intact."""
    small = image.copy()
    small.thumbnail((160, 160))
    pixels = small.load()
    xs, ys = [], []
    for y in range(small.height):
        for x in range(small.width):
            r, g, b = pixels[x, y]
            if min(r, g, b) < 238 or max(r, g, b) - min(r, g, b) > 18:
                xs.append(x)
                ys.append(y)
    if len(xs) < 20:
        return image
    sx, sy = image.width / small.width, image.height / small.height
    x0, x1 = max(0, int(min(xs) * sx) - 4), min(image.width, int((max(xs) + 1) * sx) + 4)
    y0, y1 = max(0, int(min(ys) * sy) - 4), min(image.height, int((max(ys) + 1) * sy) + 4)
    if x1 - x0 < image.width * .2 or y1 - y0 < image.height * .2:
        return image
    return image.crop((x0, y0, x1, y1))


def _features(image):
    image = _trim_white(image)
    # Normalizing the visible package rather than the surrounding whitespace makes
    # the descriptor more stable across catalog thumbnails and user photographs.
    gray = ImageOps.fit(image.convert('L'), (9, 8), method=Image.Resampling.LANCZOS)
    gray_pixels = list(gray.getdata())
    digest = tuple(gray_pixels[row * 9 + col] > gray_pixels[row * 9 + col + 1]
                   for row in range(8) for col in range(8))

    hsv = ImageOps.fit(image.convert('HSV'), (48, 48), method=Image.Resampling.BILINEAR)
    histogram = [0.0] * 16
    for hue, saturation, value in hsv.getdata():
        # White background and glare carry little information about the package.
        if saturation < 38 or value > 248:
            continue
        histogram[min(15, hue * 16 // 256)] += saturation / 255
    total = sum(histogram)
    if total:
        histogram = [value / total for value in histogram]
    return digest, histogram


def _similarity(left, right):
    left_hash, left_hist = left
    right_hash, right_hist = right
    hash_score = sum(a == b for a, b in zip(left_hash, right_hash)) / len(left_hash)
    histogram_score = sum(min(a, b) for a, b in zip(left_hist, right_hist))
    return round((.72 * hash_score + .28 * histogram_score) * 100)


@lru_cache(maxsize=256)
def _remote_features(url):
    raw = _remote_image_bytes(url)
    image = _decode(raw) if raw else None
    return _features(image) if image else None


def catalog_image_previews(offers, per_store=4):
    """Return small same-origin previews so the browser can compare with CLIP."""
    candidates = []
    counts = {}
    for index, offer in enumerate(offers):
        url = str(offer.get('image_url') or '')
        store = str(offer.get('store') or '')
        if _allowed_catalog_url(url) and counts.get(store, 0) < per_store:
            counts[store] = counts.get(store, 0) + 1
            candidates.append((index, url))

    def prepare(candidate):
        index, url = candidate
        raw = _remote_image_bytes(url)
        image = _decode(raw) if raw else None
        if not image:
            return index, None
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format='JPEG', quality=78, optimize=True)
        return index, 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode('ascii')

    previews = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        for index, data_url in pool.map(prepare, candidates):
            if data_url:
                previews[index] = data_url
    return previews


def rank_catalog_images(reference_bytes, offers, per_store=4):
    """Attach visual similarity to a small, price-leading candidate set per store."""
    reference = _decode(reference_bytes)
    if not reference:
        raise ValueError('La foto no es válida. Elegí una imagen JPG, PNG o WebP.')
    reference_features = _features(reference)
    candidates = []
    counts = {}
    for index, offer in enumerate(offers):
        url = str(offer.get('image_url') or '')
        store = str(offer.get('store') or '')
        parsed = urlparse(url)
        host = (parsed.hostname or '').lower()
        allowed = parsed.scheme == 'https' and any(host == suffix or host.endswith('.' + suffix)
                                                   for suffix in ALLOWED_IMAGE_HOSTS)
        if allowed and counts.get(store, 0) < per_store:
            counts[store] = counts.get(store, 0) + 1
            candidates.append((index, url))

    def score(candidate):
        index, url = candidate
        features = _remote_features(url)
        return index, _similarity(reference_features, features) if features else None

    with ThreadPoolExecutor(max_workers=12) as pool:
        for index, similarity in pool.map(score, candidates):
            if similarity is not None:
                offers[index]['visual_similarity'] = similarity
    # Similarity groups visually closer candidates first; price remains the tie-breaker.
    offers.sort(key=lambda offer: (offer.get('visual_similarity') is None,
                                   -(offer.get('visual_similarity') or 0),
                                   offer.get('promo_price', float('inf'))))
    compared = sum('visual_similarity' in offer for offer in offers)
    unavailable = len(candidates) - compared
    warning = f'Similitud visual aproximada calculada para {compared} fotos de producto.'
    if unavailable:
        warning += f' No se pudieron comparar {unavailable} fotos del catálogo.'
    if not compared:
        warning = 'No se pudieron comparar las fotos del catálogo; se muestran las coincidencias por texto y precio.'
    return warning
