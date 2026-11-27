import base64
from io import BytesIO
import unittest
from unittest.mock import patch

from PIL import Image

from backend.app.services import product_image_similarity as similarity


class CatalogImagePreviewTests(unittest.TestCase):
    def test_returns_small_same_origin_image_preview_for_allowed_catalog(self):
        source = Image.new('RGB', (640, 480), '#315f45')
        raw = BytesIO()
        source.save(raw, format='PNG')
        offer = {'store': 'Día', 'image_url': 'https://cdn.vtexassets.com/product.jpg'}
        with patch.object(similarity, '_remote_image_bytes', return_value=raw.getvalue()):
            previews = similarity.catalog_image_previews([offer])
        self.assertIn(0, previews)
        self.assertTrue(previews[0].startswith('data:image/jpeg;base64,'))
        decoded = base64.b64decode(previews[0].split(',', 1)[1])
        with Image.open(BytesIO(decoded)) as image:
            self.assertLessEqual(max(image.size), 256)
            self.assertEqual(image.format, 'JPEG')

    def test_skips_non_supermarket_image_hosts(self):
        with patch.object(similarity, '_remote_image_bytes') as download:
            previews = similarity.catalog_image_previews([
                {'store': 'externo', 'image_url': 'https://example.com/private.jpg'}
            ])
        self.assertEqual(previews, {})
        download.assert_not_called()


if __name__ == '__main__':
    unittest.main()
