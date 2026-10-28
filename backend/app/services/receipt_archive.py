"""Private receipt images. Downloads are exposed only through registered expenses."""
import io
import os
import re
import secrets
from pathlib import Path
from PIL import Image, ImageOps
from backend.app.core.paths import PROJECT_ROOT

ARCHIVE_DIR = Path(os.getenv('EXPENSA_RECEIPT_DIR', str(PROJECT_ROOT / 'data' / 'receipts')))


def image_path(identity):
    if not re.fullmatch(r'[a-f0-9]{32}', identity or ''):
        raise ValueError('Referencia de comprobante inválida.')
    return ARCHIVE_DIR / (identity + '.jpg')


def archive_image(content):
    identity = secrets.token_hex(16)
    # Normalize orientation and remove EXIF; preserve full resolution and all edges.
    with Image.open(io.BytesIO(content)) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        image.save(image_path(identity), format='JPEG', quality=95)
    return identity
