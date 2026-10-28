import copy
from io import BytesIO
from PIL import Image
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi import Request
from backend.app.core.security import require_member
from data import db
from backend.app.main import app
from backend.app.services import offers as offer_service
from backend.app.api.routes import offers as offer_routes
from backend.app.services.receipt_scanning import parse_receipt
from backend.app.services.snapshot_merge import merge_snapshot, SyncConflict


class Workflows(unittest.TestCase):
    def setUp(self):
        def allowed(request: Request):
            request.state.user = {"id": "test-admin", "email": "admin@example.test", "role": "admin"}
            return request.state.user
        app.dependency_overrides[require_member] = allowed
        self.addCleanup(lambda: app.dependency_overrides.pop(require_member, None))
        self.directory = tempfile.TemporaryDirectory()
        self.patches = [patch.object(db, 'DB_FILE', str(Path(self.directory.name) / 'state.json')),
                        patch.object(db, 'export_to_legacy_formats')]
        for item in self.patches:
            item.start()
        self.state = {'stock': [], 'shopping': [], 'offers': [], 'expenses': [],
                      'user_prefs': {'id': 0, 'monthlyBudget': 10000, 'totalSpent': 0}}
        db.save_db(copy.deepcopy(self.state))
        self.client = TestClient(app)

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.directory.cleanup()

    def test_parse_argentine_prices_quantities_and_printed_total(self):
        draft = parse_receipt('SUPERMERCADO\n2 x LECHE 1.500,00 3.000,00\nARROZ 1.200,00\nDESCUENTO -200,00\nTOTAL 4.000,00\nEFECTIVO 5.000,00\nVUELTO 1.000,00')
        self.assertEqual(len(draft['items']), 2)
        self.assertEqual(draft['items'][0]['quantity'], 2)
        self.assertEqual(draft['items'][0]['unit_price'], 1500)
        self.assertEqual(draft['total'], 4000)
        self.assertEqual(draft['subtotal'], 4200)
        self.assertTrue(draft['warnings'])

    def test_wrapped_receipt_description_survives_confirmation(self):
        draft = parse_receipt('SUPERMERCADO\nLECHE ENTERA\nLARGA VIDA 1 LITRO\n1.500,00\nTOTAL 1.500,00')
        self.assertEqual(draft['items'][0]['description'], 'LECHE ENTERA LARGA VIDA 1 LITRO')
        ticket = {'id': 'wrapped', 'store': 'Super', 'items': draft['items'], 'total': draft['total']}
        self.assertEqual(self.client.post('/api/receipts/confirm', json=ticket).status_code, 200)
        saved = self.client.get('/api/expenses').json()[0]
        self.assertEqual(saved['items'], draft['items'])

    @patch.object(offer_service, 'ratoneando_offers', return_value=([], 'Sin proveedor'))
    def test_web_created_offer_is_searchable_on_web_and_android(self, _):
        created = self.client.post('/api/offers/saved', json={
            'product': 'Leche entera 1 litro', 'store': 'Super local', 'price': 1500})
        self.assertEqual(created.status_code, 200)
        web = self.client.get('/api/offers/compare', params={'q': 'leche entera 1 litro'}).json()
        android = self.client.get('/offers', params={'q': 'leche entera 1 litro'}).json()
        self.assertEqual(web['top_offer']['promo_price'], 1500)
        self.assertEqual(web['top_offer']['product'], android[0]['name'])
        self.assertEqual(web['top_offer']['store'], android[0]['store'])

    def test_wrapped_product_with_quantity_and_fiscal_suffix(self):
        draft = parse_receipt('LECHE ENTERA\n2 x 1.500,00 3.000,00 A\nTOTAL 3.000,00')
        self.assertEqual(draft['items'][0]['description'], 'LECHE ENTERA')
        self.assertEqual(draft['items'][0]['quantity'], 2)
        self.assertEqual(draft['items'][0]['line_total'], 3000)

    def test_monthly_budget_rejects_negative_and_receipt_rejects_invalid_date(self):
        self.assertEqual(self.client.post('/api/budget', json={'monthlyBudget': -1}).status_code, 422)
        ticket = {'id': 'date', 'store': 'Super A', 'total': 100,
                  'items': [{'description': 'Arroz', 'quantity': 1, 'unit_price': 100, 'line_total': 100}],
                  'purchase_date': '2026-02-31'}
        self.assertEqual(self.client.post('/api/receipts/confirm', json=ticket).status_code, 422)
        self.assertEqual(self.client.get('/api/expenses').json(), [])

    def test_monthly_report_uses_purchase_date_and_argentine_midnight(self):
        from datetime import datetime, timezone
        self.state['expenses'] = [
            {'id': 'oct', 'amount': 1200, 'store': 'Super A', 'purchase_date': '2026-10-10'},
            {'id': 'nov', 'amount': 500, 'store': 'Super B', 'purchase_date': '2026-11-01'},
            {'id': 'boundary', 'amount': 300, 'note': 'Super A',
             'timestamp': int(datetime(2026, 11, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)}]
        db.save_db(self.state)
        october = self.client.get('/api/budget?month=2026-10').json()
        self.assertEqual(october['totalSpent'], 1500)
        self.assertEqual(october['remaining'], 8500)
        self.assertEqual(october['by_store'], [{'store': 'Super A', 'amount': 1500}])
        self.assertEqual(self.client.get('/api/budget?month=2026-11').json()['totalSpent'], 500)
        self.assertEqual(self.client.get('/api/budget?month=2026-13').status_code, 422)

    def test_receipt_archive_text_date_and_duplicate_do_not_double_spend(self):
        from backend.app.services import receipt_archive
        content = BytesIO()
        Image.new('RGB', (200, 400), 'white').save(content, format='PNG')
        with patch.object(receipt_archive, 'ARCHIVE_DIR', Path(self.directory.name) / 'receipts'), patch(
                'backend.app.api.routes.receipts.scan_receipt', return_value=parse_receipt('LECHE 1500,00\nTOTAL 1500,00')):
            draft = self.client.post('/api/receipts/scan', files={'image': ('ticket.png', content.getvalue(), 'image/png')}).json()
            self.assertTrue(receipt_archive.image_path(draft['receipt_image']).is_file())
            # An unconfirmed upload is never directly available as a registered expense.
            self.assertEqual(self.client.get('/api/receipts/' + draft['receipt_image'] + '/image').status_code, 404)
            ticket = {key: draft[key] for key in ('items', 'total', 'raw_text', 'receipt_image')}
            ticket.update(id='archived', store='Super A', purchase_date='2026-10-12')
            response = self.client.post('/api/receipts/confirm', json=ticket)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(self.client.post('/api/receipts/confirm', json=ticket).json()['duplicate'])
            text = self.client.get('/api/receipts/archived/text')
            self.assertEqual(text.status_code, 200)
            self.assertIn('Super A', text.text)
            self.assertIn('2026-10-12', text.text)
            self.assertIn('LECHE 1500,00', text.text)
            image = self.client.get('/api/receipts/archived/image')
            self.assertEqual(image.status_code, 200)
            self.assertEqual(Image.open(BytesIO(image.content)).size, (200, 400))
            self.assertEqual(self.client.get('/api/budget?month=2026-10').json()['totalSpent'], 1500)

    def test_confirm_receipt_updates_budget_once_and_preserves_details(self):
        ticket = {'id': 'receipt-1', 'store': 'Supermercado', 'total': 3000,
                  'items': [{'description': 'Leche', 'quantity': 2, 'unit_price': 1500, 'line_total': 3000}]}
        self.assertEqual(self.client.post('/api/receipts/confirm', json=ticket).status_code, 200)
        repeated = self.client.post('/api/receipts/confirm', json=ticket)
        self.assertTrue(repeated.json()['duplicate'])
        self.assertEqual(self.client.get('/api/budget').json()['totalSpent'], 3000)
        self.assertEqual(len(self.client.get('/api/expenses').json()), 1)
        self.assertEqual(self.client.get('/api/expenses').json()[0]['items'][0]['quantity'], 2)

    def test_reject_mismatched_unit_price_and_unexplained_total(self):
        ticket = {'id': 'bad', 'store': 'Super', 'total': 500,
                  'items': [{'description': 'Leche', 'quantity': 2, 'unit_price': 1500, 'line_total': 3000}]}
        self.assertEqual(self.client.post('/api/receipts/confirm', json=ticket).status_code, 422)
        ticket['adjustment_note'] = 'Descuento'
        self.assertEqual(self.client.post('/api/receipts/confirm', json=ticket).status_code, 200)
        ticket['id'] = 'other'
        ticket['items'][0]['line_total'] = 2000
        self.assertEqual(self.client.post('/api/receipts/confirm', json=ticket).status_code, 422)

    def test_menu_buttons_and_numbers_share_actions(self):
        for message, action in [('1', 'comparator'), ('opción 2', 'budget'), ('3', 'stock')]:
            response = self.client.post('/api/ai/chat', json={'message': message})
            self.assertEqual(response.json()['action'], action)

    @patch.object(offer_service, 'ratoneando_offers', return_value=([], 'Sin proveedor'))
    def test_voice_phrases_filter_exact_product_and_sort_by_discount_or_price(self, _):
        self.state['offers'] = [
            {'id': '1', 'product': 'Leche entera', 'store': 'A', 'price': '$1.200', 'saving': '10% off'},
            {'id': '2', 'product': 'Leche entera', 'store': 'B', 'price': '$1.500', 'saving': '25% off'},
            {'id': '3', 'product': 'Arroz', 'store': 'C', 'price': '$800', 'saving': '50% off'}]
        db.save_db(self.state)
        result = offer_service.compare_supermarket_offers('Quiero saber la oferta top de leche entera')
        self.assertEqual(result['top_offer']['store'], 'B')
        self.assertEqual(len(result['offers']), 2)
        self.assertEqual(offer_service.compare_supermarket_offers('leche entera', 'price')['top_offer']['store'], 'A')
        self.assertEqual(offer_service.compare_supermarket_offers('producto inexistente')['offers'], [])
        chat = self.client.post('/api/ai/chat', json={'message': 'leche entera', 'context': 'offers'}).json()
        self.assertEqual(chat['comparison']['top_offer']['store'], 'B')

    @patch.object(offer_service, 'ratoneando_offers', return_value=([], 'Sin proveedor'))
    def test_equivalent_sizes_and_unknown_presentation(self, _):
        self.state['offers'] = [
            {'id': 'unknown', 'product': 'Leche entera', 'store': 'A', 'price': 800},
            {'id': 'litre', 'product': 'Leche entera 1L', 'store': 'B', 'price': 1500},
            {'id': 'large', 'product': 'Leche entera 1,5 litros', 'store': 'C', 'price': 1300},
            {'id': 'skim', 'product': 'Leche descremada 1000 ml', 'store': 'D', 'price': 900}]
        db.save_db(self.state)
        for query in ('leche entera de 1 lt', 'leche entera un litro', 'leche entera 1000ml'):
            result = offer_service.compare_supermarket_offers(query, 'price')
            self.assertEqual([o['id'] for o in result['offers']], ['litre', 'unknown'])
            self.assertEqual(result['top_offer']['id'], 'litre')
            unknown = result['offers'][1]
            self.assertFalse(unknown['size_confirmed'])
            self.assertIn('Presentación sin confirmar', unknown['conditions'])
        self.assertEqual(offer_service.clean_query('Aceite 1,5 L'), offer_service.clean_query('Aceite 1500 cc'))
        self.assertEqual(offer_service.clean_query('Arroz 1 kg'), offer_service.clean_query('Arroz 1000 gramos'))
        self.state['offers'] = self.state['offers'][:1]
        db.save_db(self.state)
        result = offer_service.compare_supermarket_offers('leche entera de 1 lt')
        self.assertEqual(len(result['offers']), 1)
        self.assertIn('no está confirmada', result['ai_analysis']['verdict'])
        self.state['offers'][0]['price'] = ''
        db.save_db(self.state)
        result = offer_service.compare_supermarket_offers('leche entera de 1 lt')
        self.assertEqual(result['offers'], [])
        self.assertIn('precio válido', result['warning'])
        self.assertIn('falta un precio válido', result['ai_analysis']['verdict'])

    def test_saved_offer_photo_is_validated_and_used_in_comparison(self):
        self.state['offers'] = [{'id':'saved', 'product':'Leche entera', 'store':'A', 'price':''}]
        db.save_db(self.state)
        updated = self.client.patch('/api/offers/saved/saved', json={'product':'Leche entera 1 litro', 'price':1200})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.patch('/api/offers/saved/saved', json={'product':'Leche', 'price':-1}).status_code, 422)
        self.assertEqual(self.client.post('/api/offers/saved/saved/image', files={'image':('bad.png', b'not an image', 'image/png')}).status_code, 422)
        with patch.object(offer_routes, 'IMAGE_DIR', Path(self.directory.name) / 'images'):
            photo = BytesIO(); Image.new('RGB',(10,10),'green').save(photo, format='PNG')
            uploaded = self.client.post('/api/offers/saved/saved/image', files={'image':('photo.png', photo.getvalue(), 'image/png')})
            self.assertEqual(uploaded.status_code, 200, uploaded.text)
            url = uploaded.json()['image_url']
            fetched = self.client.get(url)
            self.assertEqual(fetched.status_code, 200)
            self.assertEqual(fetched.headers['content-type'], 'image/jpeg')
            with patch.object(offer_service, 'ratoneando_offers', return_value=([], '')):
                result = offer_service.compare_supermarket_offers('leche entera 1lt')
            self.assertEqual(result['top_offer']['image_url'], url)

    def test_sync_retains_new_web_ticket_when_phone_changes_stock(self):
        baseline = copy.deepcopy(self.state)
        remote = copy.deepcopy(baseline)
        remote['expenses'] = [{'id': 'web-ticket', 'amount': 3000, 'items': [{'description': 'Leche'}]}]
        remote['user_prefs']['totalSpent'] = 3000
        local = copy.deepcopy(baseline)
        local['stock'] = [{'id': 'phone', 'name': 'Arroz'}]
        db.save_db(remote)
        response = self.client.post('/api/sync', json={**local, 'baseline': baseline})
        self.assertEqual(response.status_code, 200)
        merged = response.json()['data']
        self.assertEqual(merged['expenses'], remote['expenses'])
        self.assertEqual(merged['stock'], local['stock'])
        self.assertEqual(merged['user_prefs']['totalSpent'], 3000)

    def test_sync_conflict_does_not_write(self):
        baseline = copy.deepcopy(self.state)
        baseline['stock'] = [{'id': 'x', 'stockQuantity': 2}]
        remote, local = copy.deepcopy(baseline), copy.deepcopy(baseline)
        remote['stock'][0]['stockQuantity'] = 1
        local['stock'][0]['stockQuantity'] = 0
        db.save_db(remote)
        response = self.client.post('/api/sync', json={**local, 'baseline': baseline})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(db.load_db()['stock'][0]['stockQuantity'], 1)

    def test_first_pairing_preserves_remote_and_imports_local_expenses_once(self):
        local = copy.deepcopy(self.state)
        local['expenses'] = [{'id': 'phone', 'amount': 1500}]
        first = merge_snapshot(self.state, local)
        second = merge_snapshot(first, local)
        self.assertEqual(second['user_prefs']['totalSpent'], 1500)

    def test_corrupt_database_is_never_reset(self):
        Path(db.DB_FILE).write_text('{broken', encoding='utf-8')
        with self.assertRaises(RuntimeError):
            db.load_db()
        self.assertEqual(Path(db.DB_FILE).read_text(encoding='utf-8'), '{broken')

    def test_price_formats_and_nonfinite_values(self):
        for value in ('$1.500,25', '$1,500.25', 1500.25):
            self.assertEqual(offer_service.money(value), 1500.25)
        self.assertEqual(offer_service.money('$1.500'), 1500)
        self.assertIsNone(offer_service.money(float('nan')))

    @patch.object(offer_service, 'ratoneando_offers', return_value=([], ''))
    def test_second_unit_discount_is_not_single_unit_discount(self, _):
        self.state['offers'] = [{'id': 'bulk', 'product': 'Leche', 'store': 'A',
                                 'price': 1500, 'saving': '2do al 70%'}]
        db.save_db(self.state)
        offer = offer_service.compare_supermarket_offers('leche')['top_offer']
        self.assertEqual(offer['saving_percent'], 35)
        self.assertEqual(offer['promo_price'], 1500)
        self.assertTrue(offer['conditions'])


if __name__ == '__main__':
    unittest.main()
