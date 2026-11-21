const { test, expect } = require('@playwright/test');

// Authenticate once per worker; exercise normal sessions without triggering the login throttle.
let sessionCookies = null;
test.beforeEach(async ({page, context}) => {
  if (sessionCookies) await context.addCookies(sessionCookies);
  await page.goto('/');
  if (!sessionCookies) {
    await page.locator('#auth-email').fill('qa_household');
    await page.locator('#auth-password').fill('SoloParaQA_2026_SinDatosReales');
    await page.locator('#auth-submit').click();
  }
  await expect(page.locator('#app-shell')).toBeVisible();
  if (!sessionCookies) sessionCookies = await context.cookies();
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
  await page.route('**/api/receipts/draft*', route => route.abort('connectionfailed'));
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
  const externalQuery = new URL(await page.locator('#ratoneando-search').getAttribute('href'));
  expect(externalQuery.origin).toBe('https://ratoneando.ar');
  expect(externalQuery.searchParams.get('q')).toBe('arroz qa 1000g');
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

test('WEB-05: corregir OCR conserva imagen y guarda descuento/neto en el mes de compra', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#receipt-photo').setInputFiles(require('path').join(__dirname,'../fixtures/ticket-sintetico.png'));
  await page.locator('#receipt-scan').click();
  await expect(page.locator('#receipt-lines tr')).toHaveCount(2, {timeout:60000});
  await page.locator('#receipt-parse').click();
  await expect(page.locator('#receipt-status')).toContainText('Revisá descripción');
  const first = page.locator('#receipt-lines tr').first();
  await expect(first.locator('[data-field="detail"]')).toHaveCount(0);
  await expect(first.locator('[data-field="discount"]')).toBeHidden();
  await first.locator('[data-field="line_total"]').fill('1350.00');
  await expect(first.locator('[data-field="line_total"]')).toHaveValue('1350.00');
  await page.locator('#receipt-total').fill('2550');
  await page.locator('#receipt-store').fill('Super descuento QA');
  await page.locator('#receipt-date').fill('2026-12-05');
  await page.locator('#receipt-confirm').click();
  await expect(page.locator('#receipt-status')).toContainText('Ticket registrado');
  await expect(page.locator('#expense-month')).toHaveValue('2026-12');
  await expect(page.locator('#budget-spent-text')).toContainText('2.550');
  await page.locator('#expense-receipt-date').selectOption('2026-12-05');
  await expect(page.locator('#expense-products-body')).toContainText('2026-12-05');
  await expect(page.locator('#expense-products-body')).toContainText('1.350,00');
  const image = await page.getByText('Ver comprobante').getAttribute('href');
  expect((await page.request.get(image)).status()).toBe(200);
});

test('WEB-06: API sin conexión muestra diagnóstico y no una excepción JSON', async ({page}) => {
  await page.route('**/api/offers/compare*', route => route.fulfill({status:502,contentType:'text/html',body:'Backend unavailable'}));
  await page.locator('#ai-search-input').fill('leche');
  await page.locator('#btn-ai-search').click();
  await expect(page.locator('#offer-source-status')).toContainText('backend esté activo');
});

test('WEB-07: descargar el lector pausa la sincronización y luego la reanuda', async ({page}) => {
  await page.clock.install();
  await page.reload();
  await expect(page.locator('#app-shell')).toBeVisible();
  await expect(page.locator('.sync-text')).toHaveText('Sincronizado');
  let release;
  const held = new Promise(resolve => { release = resolve; });
  let downloading = false;
  await page.route('**/lang/spa.traineddata.gz', async route => {
    downloading = true;
    await held;
    await route.continue();
  });
  let stockRequests = 0;
  page.on('request', request => { if (new URL(request.url()).pathname === '/api/stock') stockRequests++; });
  try {
    await page.locator('[data-tab="budget"]').click();
    await page.locator('#receipt-photo').setInputFiles(require('path').join(__dirname,'../fixtures/ticket-sintetico.png'));
    await page.locator('#receipt-scan').click();
    await expect.poll(() => downloading).toBe(true);
    const before = stockRequests;
    await page.clock.fastForward(16000);
    expect(stockRequests).toBe(before);
    release();
    await expect(page.locator('#receipt-lines tr')).toHaveCount(2,{timeout:30000});
    await page.clock.fastForward(16000);
    await expect.poll(() => stockRequests).toBeGreaterThan(before);
  } finally { release(); }
});


test('WEB-08: IVA incluido se conserva sin descontarlo dos veces', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#receipt-text').fill('CUIT 30-00000000-0\nLECHE QA 1500,00 1400,00\nTOTAL 1400,00\nIVA CONTENIDO 21% 242,98');
  await page.locator('#receipt-parse').click();
  await expect(page.locator('#receipt-lines tr')).toHaveCount(1);
  await expect(page.locator('#receipt-vat')).toHaveValue('242.98');
  await expect(page.locator('#receipt-vat-included')).toBeChecked();
  await expect(page.locator('[data-field="discount"]')).toHaveValue('100');
  await page.locator('#receipt-store').fill('IVA QA');
  await page.locator('#receipt-date').fill('2026-09-15');
  await page.locator('#receipt-confirm').click();
  await expect(page.locator('#receipt-status')).toContainText('Ticket registrado');
  const saved = (await (await page.request.get('/api/expenses')).json()).find(e => e.store === 'IVA QA');
  expect(saved.amount).toBe(1400);
  expect(saved.vat_amount).toBe(242.98);
  await expect(page.locator('#budget-spent-text')).toContainText('1.400');
});


test('WEB-09: cargar ticket abre el selector y seleccionar la foto inicia su lectura', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  const chooserPromise = page.waitForEvent('filechooser');
  await page.locator('#receipt-scan').click();
  const chooser = await chooserPromise;
  await chooser.setFiles(require('path').join(__dirname,'../fixtures/ticket-sintetico.png'));
  await expect(page.locator('#receipt-lines tr')).toHaveCount(2, {timeout:60000});
  await expect(page.locator('#receipt-total')).toHaveValue('2700');
});


test('WEB-10: resumen por fecha conserva el precio de cada compra anterior', async ({page}) => {
  for (const [id,date,price] of [['old-qa','2026-07-01',1000],['new-qa','2026-07-15',1200]]) {
    const response = await page.evaluate(async ({id,date,price}) => {
      const result = await fetch('/api/receipts/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,store:'Histórico QA',purchase_date:date,total:price,items:[{description:'ARROZ HISTÓRICO QA',quantity:1,unit_price:price,line_total:price}]})});
      return {ok:result.ok,body:await result.text()};
    },{id,date,price});
    expect(response.ok, response.body).toBeTruthy();
  }
  await page.reload();
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#expense-month').fill('2026-07');
  await expect(page.locator('#expense-products-body tr')).toHaveCount(2);
  await page.locator('#expense-receipt-date').selectOption('2026-07-01');
  await expect(page.locator('#expense-products-body tr')).toHaveCount(1);
  await expect(page.locator('#expense-products-body')).toContainText('1.000,00');
  await expect(page.locator('#expense-products-body')).not.toContainText('1.200,00');
  await page.locator('#expense-receipt-date').selectOption('2026-07-15');
  await expect(page.locator('#expense-products-body')).toContainText('1.200,00');
});


test('WEB-11: foto con letra pequeña y sombras conserva nombres completos y precios', async ({page}) => {
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#receipt-preprocessing').selectOption('adaptive');
  await page.locator('#receipt-photo').setInputFiles(require('path').join(__dirname,'../fixtures/ticket-pequeno-sombras.png'));
  await expect(page.locator('#receipt-lines tr')).toHaveCount(2,{timeout:60000});
  await expect(page.locator('[data-field="description"]').first()).toHaveValue('LECHE ENTERA LARGA VIDA QA');
  await expect(page.locator('[data-field="description"]').last()).toHaveValue('ARROZ INTEGRAL QA');
  await expect(page.locator('#receipt-total')).toHaveValue('4200');
});


test('WEB-12: ticket local DIA permite revisar la presentación y confirmar el presupuesto', async ({page}) => {
  test.skip(!process.env.E2E_RECEIPT_FIXTURE, 'Requiere foto local autorizada; no se incluye en Git.');
  await page.locator('[data-tab="budget"]').click();
  await page.locator('#receipt-photo').setInputFiles(process.env.E2E_RECEIPT_FIXTURE);
  await expect(page.locator('#receipt-review')).toBeVisible({timeout:60000});
  await expect(page.locator('#receipt-lines tr')).toHaveCount(1);
  await expect(page.locator('[data-field="description"]')).toHaveValue(/^CUNNING\s+COLA\s+2[.,]25\s*[L1]$/i);
  await expect(page.locator('[data-field="quantity"]')).toHaveValue('2');
  await expect(page.locator('[data-field="unit_price"]')).toHaveValue('2749');
  await expect(page.locator('[data-field="line_total"]')).toHaveValue('5498');
  await expect(page.locator('#receipt-total')).toHaveValue('5498');
  await expect(page.locator('#receipt-vat')).toHaveValue('954.2');
  await expect(page.locator('#receipt-store')).toHaveValue('DIA');
  await page.locator('[data-field="description"]').fill('CUNNING COLA 2,25L');
  await page.locator('#receipt-confirm').click();
  await expect(page.locator('#receipt-status')).toContainText('Ticket registrado');
  await expect(page.locator('#budget-spent-text')).toContainText('5.498');
});


test('WEB-13: leche por marca y tamaño excluye alimentos que la mencionan',async({page})=>{
  await page.evaluate(async()=>{
    for(const product of ['Leche La Serenísima 1L','Galletitas con leche La Serenísima 1L','Leche La Serenísima 1,5L','Leche otra marca 1L','Leche La Serenísima pack 6x1L']){
      const response=await fetch('/api/offers/saved',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product,store:'Relevancia QA',price:1500})});
      if(!response.ok)throw new Error(await response.text());
    }
  });
  await page.locator('#ai-search-input').fill('Quiero encontrar leche LaSerenisima de 1 litro');
  await page.locator('#btn-ai-search').click();
  await expect(page.locator('.store-card')).toHaveCount(1);
  await expect(page.locator('.store-product-title')).toHaveText('Leche La Serenísima 1L');
  await page.locator('#ai-search-input').fill('arroz');
  await expect(page.locator('#comparator-results')).toBeHidden();
});


test('WEB-14: faltantes consulta nombre marca y presentación del stock', async ({page}) => {
  await page.route('**/api/stock', route => route.fulfill({json:[{id:'qa-milk',name:'Leche',brand:'La Serenísima',unit:'1 L',category:'Comestibles',stockQuantity:0,inUseCount:0}]}));
  await page.reload();
  await expect(page.locator('#critical-quick-chips .chip')).toHaveCount(1);
  const request = page.waitForRequest(r => r.url().includes('/api/offers/compare?'));
  await page.locator('#critical-quick-chips .chip').click();
  expect(new URL((await request).url()).searchParams.get('q')).toBe('Leche La Serenísima 1 L');
  await expect(page.locator('#ai-search-input')).toHaveValue('Leche La Serenísima 1 L');
});


test('WEB-15: supermercado encabeza la tarjeta y top identifica el menor precio', async ({page}) => {
  const cheap = {id:'cheap',store:'Supermercado Económico',product:'Leche QA 1L',brand:'QA',promo_price:1000,promo_text:'Precio publicado',conditions:'',source:'Prueba local',saving_percent:0};
  const discount = {...cheap,id:'discount',store:'Supermercado Descuento',promo_price:1500,saving_percent:30};
  await page.route('**/api/offers/compare*', route => route.fulfill({json:{offers:[discount,cheap],top_offer:cheap,product_name:'Leche QA 1L',category:'Comestibles',ai_analysis:{best_single:{store:cheap.store,price:1000},max_saving_percent:30,verdict:'Oferta top por menor precio'}}}));
  await expect(page.locator('#offer-sort')).toHaveValue('price');
  await page.locator('#ai-search-input').fill('Leche QA 1L');
  await page.locator('#btn-ai-search').click();
  await expect(page.locator('.store-card')).toHaveCount(2);
  await expect(page.locator('.store-card').first().locator(':scope > :first-child')).toHaveText(discount.store);
  await expect(page.locator('.is-winner .offer-store-title')).toHaveText(cheap.store);
  await expect(page.locator('.top-offer-label')).toHaveText('🏆 Oferta top · menor precio');
});


test('WEB-16: ticket compacto muestra fecha y comercio y abre la foto por doble clic', async ({page}) => {
  await page.route('**/api/expenses', route => route.fulfill({json:[{id:'receipt-view',store:'Día QA',purchase_date:'2026-11-15',amount:5498,items:[{description:'CUNNING COLA 2,25L',quantity:2,unit_price:2749,line_total:5498}]}]}));
  await page.route('**/api/receipts/receipt-view/image', route => route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jf1sAAAAASUVORK5CYII=', 'base64')}));
  await page.reload();
  const ticket = page.locator('#offer-receipt-list .saved-receipt-row');
  await expect(ticket).toHaveCount(1);
  await expect(ticket).toContainText('2026-11-15');
  await expect(ticket).toContainText('Día QA');
  await expect(ticket).not.toContainText('CUNNING');
  await expect(ticket).not.toContainText('5498');
  await ticket.click();
  await expect(page.locator('#saved-receipt-dialog')).not.toBeVisible();
  await ticket.dblclick();
  await expect(page.locator('#saved-receipt-dialog')).toBeVisible();
  await expect(page.locator('#saved-receipt-content')).toContainText('CUNNING COLA 2,25L');
  await expect(page.locator('.saved-receipt-photo')).toHaveAttribute('src',/^blob:/);
  await page.locator('#saved-receipt-close').click();
  await expect(page.locator('#saved-receipt-dialog')).not.toBeVisible();
});
