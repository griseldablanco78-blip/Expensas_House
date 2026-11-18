"""Private receipt images. Downloads are exposed only through registered expenses."""
import io
import os
import re
import secrets
from pathlib import Path
from PIL import Image, ImageOps
from backend.app.core.paths import PROJECT_ROOT
from backend.app.infrastructure import cloud_storage

ARCHIVE_DIR = Path(os.getenv('EXPENSA_RECEIPT_DIR', str(PROJECT_ROOT / 'data' / 'receipts')))


def image_path(identity):
    if not re.fullmatch(r'[a-f0-9]{32}', identity or ''):
        raise ValueError('Referencia de comprobante inválida.')
    return ARCHIVE_DIR / (identity + '.jpg')


def archive_image(content):
    identity = secrets.token_hex(16)
    # Normalize orientation and remove EXIF; preserve full resolution and all edges.
    with Image.open(io.BytesIO(content)) as original:
        if original.width * original.height > 25_000_000:
            raise ValueError('La imagen supera 25 megapíxeles.')
        image = ImageOps.exif_transpose(original).convert('RGB')
        if cloud_storage.enabled():
            image.thumbnail((2000,6000))
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=88)
            cloud_storage.put('receipts/'+identity+'.jpg', buffer.getvalue())
            return identity
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        image.save(image_path(identity), format='JPEG', quality=95)
    return identity


def image_exists(identity):
    image_path(identity)
    return cloud_storage.exists('receipts/'+identity+'.jpg') if cloud_storage.enabled() else image_path(identity).is_file()


def read_image(identity):
    image_path(identity)
    return cloud_storage.get('receipts/'+identity+'.jpg') if cloud_storage.enabled() else image_path(identity).read_bytes()
