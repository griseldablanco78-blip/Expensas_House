import io
import json
import unittest
from unittest.mock import patch
from backend.app.services import catalog_search


class PublicCatalogTests(unittest.TestCase):
    def test_only_available_real_prices_are_returned_with_source(self):
        payload = [{'productId':'p1', 'productName':'Leche entera 1 L', 'brand':'Marca QA', 'link':'https://example.test/p',
                    'items':[{'itemId':'sku1','images':[{'imageUrl':'https://example.test/photo.jpg'}],
                              'sellers':[{'commertialOffer':{'Price':1200,'ListPrice':1500,'AvailableQuantity':10}}]},
                             {'itemId':'sku2', 'sellers':[{'commertialOffer':{'Price':0,'AvailableQuantity':10}}]}]}]
        with patch.object(catalog_search, 'urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as request:
            offers = catalog_search.fetch_catalog('Carrefour','https://example.test','leche entera')
        self.assertIn('ft=leche%20entera', request.call_args.args[0].full_url)
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0]['price'],1200)
        self.assertEqual(offers[0]['saving'],'20.0%')
        self.assertEqual(offers[0]['source'],'Catálogo web de Carrefour')

    def test_variant_name_preserves_presentation_when_title_is_generic(self):
        payload=[{'productName':'Leche La Serenísima','brand':'La Serenísima','items':[
            {'itemId':'one','name':'Envase 1L','sellers':[{'commertialOffer':{'Price':1500,'AvailableQuantity':2}}]}]}]
        with patch.object(catalog_search,'urlopen',return_value=io.BytesIO(json.dumps(payload).encode())):
            offers=catalog_search.fetch_catalog('QA','https://example.test','leche')
        self.assertIn('1L',offers[0]['product'])

    def test_source_failure_preserves_other_source_and_cache(self):
        def source(name, base, query):
            if name == 'Jumbo': raise TimeoutError()
            return [{'product':'Leche', 'price':1200}]
        with patch.dict(catalog_search._CACHE, {}, clear=True), patch.object(catalog_search, 'fetch_catalog', side_effect=source) as fetch:
            offers, warning = catalog_search.catalog_offers('leche')
            self.assertEqual(len(offers),len(catalog_search.STORES)-1)
            self.assertIn('Jumbo',warning)
            self.assertEqual(catalog_search.catalog_offers('leche')[0],offers)
            self.assertEqual(fetch.call_count,len(catalog_search.STORES))


class CotoCatalogTests(unittest.TestCase):
    def test_single_unit_price_is_scoped_to_store_and_not_conditional_promotion(self):
        from backend.app.services.coto_catalog import parse_coto
        payload={'response':{'results':[{'value':'Leche QA 1L','data':{
            'id':'one','store_availability':['200'], 'product_brand':'QA',
            'price':[{'store':'090','listPrice':800},{'store':'200','listPrice':1500}],
            'discounts':[{'takingText':'Llevando 2','discountPrice':'$900'}],
            'image_url':'https://example.test/milk.jpg','url':'_/R-one'}},
            {'value':'Sin stock','data':{'id':'two','store_availability':['090'],'price':[{'store':'200','listPrice':700}]}}]}}
        rows=parse_coto(payload)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['price'],1500)
        self.assertEqual(rows[0]['saving'],'')
        self.assertEqual(rows[0]['store'],'Coto')
        self.assertTrue(rows[0]['direct_link'].startswith('https://www.cotodigital.com.ar/'))

    def test_public_search_configuration_is_discovered_and_cached(self):
        from backend.app.services import coto_catalog
        with patch.object(coto_catalog,'_CONFIG',None), patch.object(coto_catalog,'public_bytes',side_effect=[
            b'<script src="/main.abc123.js"></script>', b'constructor:{apiKey:"public-search-id"}']) as source:
            self.assertEqual(coto_catalog.search_config(),'public-search-id')
            self.assertEqual(coto_catalog.search_config(),'public-search-id')
            self.assertEqual(source.call_count,2)
