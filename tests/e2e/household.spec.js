const { test, expect } = require('@playwright/test');

test.beforeEach(async ({page}) => {
  await page.goto('/');
  await page.locator('#auth-email').fill('qa-owner');
  await page.locator('#auth-password').fill('Solo para pruebas locales 2026');
  await page.locator('#auth-submit').click();
  await expect(page.locator('#app-shell')).toBeVisible();
});

test('WEB-01: ticket revisado, detalle descargable y descuento por mes', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#receipt-text').fill('LECHE ENTERA\n1500,00\nTOTAL 1500,00');
  await page.locator('#receipt-parse').click();
  await expect(page.locator('#receipt-review')).toBeVisible();
  await page.locator('#receipt-store').fill('Supermercado QA');
  await page.locator('#receipt-date').fill('2026-10-15');
  await page.locator('#receipt-confirm').click();
  await expect(page.locator('#receipt-status')).toContainText('Ticket registrado');
  await page.locator('#expense-month').fill('2026-10');
  await expect(page.locator('#expenses-table-body')).toContainText('Supermercado QA');
  await expect(page.locator('#budget-spent-text')).toContainText('1.500');
  await expect(page.locator('#budget-remaining-display')).toContainText('8.500');
  await page.getByText('Ver 1 productos').click();
  await expect(page.locator('#expenses-table-body')).toContainText('LECHE ENTERA');
  const downloadPromise = page.waitForEvent('download');
  await page.getByText('Descargar texto').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('comprobante.txt');
  expect(require('fs').readFileSync(await download.path(), 'utf8')).toContain('LECHE ENTERA');
  await page.locator('#expense-month').fill('2026-11');
  await expect(page.locator('#budget-spent-text')).toHaveText('Total gastado: $0');
});

test('WEB-02: falla de red al subir una foto no registra gastos y permite reintentar', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  const expensesBefore = await (await page.request.get('/api/expenses')).json();
  // Minimal PNG fixture; network is intentionally unavailable before OCR.
  await page.locator('#receipt-photo').setInputFiles({name:'ticket.png', mimeType:'image/png',
    buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jf1sAAAAASUVORK5CYII=', 'base64')});
  await page.route('**/api/receipts/scan*', route => route.abort('connectionfailed'));
  await page.locator('#receipt-scan').click();
  await expect(page.locator('#receipt-status')).not.toHaveText('Leyendo ticket…');
  await expect(page.locator('#receipt-status')).not.toBeEmpty();
  await expect(page.locator('#receipt-review')).toBeHidden();
  expect(await (await page.request.get('/api/expenses')).json()).toEqual(expensesBefore);
  expect(await page.locator('#receipt-photo').evaluate(input => input.files.length)).toBe(1);
  await expect(page.locator('#receipt-scan')).toBeEnabled();
});

test('WEB-03: oferta creada en la web aparece en la búsqueda real', async ({page}) => {
  await page.locator('.offer-editor summary').click();
  await page.locator('#saved-offer-product').fill('Arroz QA 1 kg');
  await page.locator('#saved-offer-store').fill('Super QA');
  await page.locator('#saved-offer-price').fill('1200');
  await page.locator('#saved-offer-form [type="submit"]').click();
  await expect(page.locator('#saved-offer-status')).toContainText('Oferta guardada');
  await page.locator('#ai-search-input').fill('Arroz QA 1 kg');
  await page.locator('#btn-ai-search').click();
  await expect(page.locator('#supermarket-cards-container')).toContainText('Super QA');
});

test('WEB-04: foto legible pasa por Tesseract y permite revisar el detalle', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#receipt-photo').setInputFiles(require('path').join(__dirname, '../fixtures/ticket-sintetico.png'));
  await expect(page.locator('#receipt-preview')).toBeVisible();
  await page.locator('#receipt-scan').click();
  await expect(page.locator('#receipt-review')).toBeVisible({timeout:60000});
  await expect(page.locator('#receipt-lines tr')).toHaveCount(2);
  await expect(page.locator('#receipt-total')).toHaveValue('2700');
});
