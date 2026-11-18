function setupReceiptScanner() {
  const byId = id => document.getElementById(id);
  const status = byId('receipt-status');
  const rows = byId('receipt-lines');
  const storageKey = `expensa_pending_receipt_${window.currentUser.id}`;
  let draftId = null;
  let receiptImage = '';
  byId('receipt-date').value = new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires', year:'numeric', month:'2-digit', day:'2-digit'}).format(new Date());
  let pending = null;
  try { pending = JSON.parse(localStorage.getItem(storageKey) || 'null'); } catch { localStorage.removeItem(storageKey); }
  let busy = false;

  function addLine(item = {}) {
    const row = document.createElement('tr');
    ['description', 'detail', 'quantity', 'unit_price', 'discount', 'line_total'].forEach(field => {
      const cell = row.insertCell();
      const input = document.createElement(['description', 'detail'].includes(field) ? 'textarea' : 'input');
      input.dataset.field = field;
      if (['description', 'detail'].includes(field)) { input.rows = 3; } else { input.type = 'number'; }
      if (input.type === 'number') { input.min = field === 'discount' ? '0' : '.01'; input.step = '.01'; }
      input.value = item[field] ?? (field === 'quantity' ? 1 : field === 'discount' ? 0 : '');
      input.setAttribute('aria-label', {description:'Producto', detail:'Detalle', quantity:'Cantidad', unit_price:'Precio unitario', discount:'Descuento', line_total:'Importe neto'}[field]);
      input.addEventListener('input', () => {
        if (['quantity', 'unit_price', 'discount'].includes(field)) {
          row.querySelector('[data-field=line_total]').value =
            (Number(row.querySelector('[data-field=quantity]').value) * Number(row.querySelector('[data-field=unit_price]').value) - Number(row.querySelector('[data-field=discount]').value)).toFixed(2);
        }
      });
      cell.appendChild(input);
    });
    const remove = document.createElement('button');
    remove.textContent = 'Quitar';
    remove.type = 'button';
    remove.addEventListener('click', () => row.remove());
    row.insertCell().appendChild(remove);
    rows.appendChild(row);
  }

  async function readReceipt(photo) {
    if (busy || pending) { status.textContent = 'Primero reintentá guardar el ticket pendiente.'; return; }
    busy = true;
    window.receiptProcessing = true;
    status.textContent = 'Leyendo ticket…';
    try {
      let body, headers = {};
      if (photo) {
        const file = byId('receipt-photo').files[0];
        if (!file) throw new Error('Elegí una foto del ticket.');
        const recognized = await browserReceiptOcr(file, byId('receipt-preprocessing').value, message => { status.textContent = message; });
        body = new FormData(); body.append('image', recognized.image, 'ticket.jpg'); body.append('text',recognized.text);
      } else {
        body = JSON.stringify({text: byId('receipt-text').value});
        headers['Content-Type'] = 'application/json';
      }
      const response = await fetch(`/api/receipts/${photo ? 'draft' : 'parse'}`, {method:'POST', headers, body});
      const data = await readApiJson(response);
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'No se pudo leer el ticket.');
      draftId = crypto.randomUUID ? crypto.randomUUID() : `receipt-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      if (photo) receiptImage = data.receipt_image || '';
      rows.replaceChildren(); data.items.forEach(addLine);
      byId('receipt-text').value = data.raw_text;
      byId('receipt-total').value = data.total;
      byId('receipt-vat').value = data.vat_amount ?? '';
      byId('receipt-vat-included').checked = data.vat_included !== false;
      byId('receipt-adjustment').value = '';
      byId('receipt-review').classList.remove('hidden');
      status.textContent = ['Revisá descripción, cantidad, precio y total.', ...data.warnings].join(' ');
    } catch (error) { status.textContent = error.message; }
    finally { busy = false; window.receiptProcessing = false; }
  }

  let previewUrl = null;
  byId('receipt-photo').addEventListener('change', () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    const photo = byId('receipt-photo').files[0];
    const preview = byId('receipt-preview');
    preview.classList.toggle('hidden', !photo);
    if (photo) { previewUrl = URL.createObjectURL(photo); preview.src = previewUrl; }
    else { previewUrl = null; preview.removeAttribute('src'); }
  });
  byId('receipt-scan').addEventListener('click', () => readReceipt(true));
  byId('receipt-parse').addEventListener('click', () => readReceipt(false));
  byId('receipt-add-line').addEventListener('click', () => addLine());
  byId('receipt-confirm').addEventListener('click', async () => {
    if (busy) return;
    try {
      if (!pending) {
        const items = [...rows.children].map(row => Object.fromEntries([...row.querySelectorAll('input, textarea')].map(input =>
          [input.dataset.field, input.type === 'number' ? Number(input.value) : input.value.trim()])));
        const store = byId('receipt-store').value.trim();
        const total = Number(byId('receipt-total').value);
        if (!store || !items.length || !total || items.some(i => !i.description || !Number.isFinite(i.quantity) || !Number.isFinite(i.unit_price) || !Number.isFinite(i.line_total) || !Number.isFinite(i.discount) || i.quantity <= 0 || i.unit_price <= 0 || i.line_total <= 0 || i.discount < 0))
          throw new Error('Completá el supermercado, los productos y todos los importes positivos.');
        if (!byId('receipt-date').value) throw new Error('Elegí la fecha de compra.');
        pending = {id: draftId, store, total, items, vat_amount:byId('receipt-vat').value === '' ? null : Number(byId('receipt-vat').value), vat_included:byId('receipt-vat-included').checked, purchase_date:byId('receipt-date').value, raw_text:byId('receipt-text').value, receipt_image:receiptImage, adjustment_note: byId('receipt-adjustment').value.trim()};
        localStorage.setItem(storageKey, JSON.stringify(pending));
      }
      busy = true; byId('receipt-confirm').disabled = true;
      status.textContent = 'Registrando el ticket…';
      const response = await fetch('/api/receipts/confirm', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(pending)});
      const data = await readApiJson(response);
      if (!response.ok) {
        if (response.status >= 400 && response.status < 500) {
          pending = null; localStorage.removeItem(storageKey);
        }
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Revisá los importes del ticket.');
      }
      const savedMonth = (data.expense?.purchase_date || pending.purchase_date || '').slice(0, 7);
      if (savedMonth) { state.expenseMonth = savedMonth; byId('expense-month').value = savedMonth; }
      pending = null; localStorage.removeItem(storageKey);
      byId('receipt-review').classList.add('hidden');
      status.textContent = 'Ticket registrado. El total se descontó del presupuesto disponible.';
      await loadAllData();
    } catch (error) {
      status.textContent = error.message + (pending ? ' Reintentá: se enviará el mismo ticket sin duplicar el gasto.' : '');
    } finally { busy = false; byId('receipt-confirm').disabled = false; }
  });
  if (pending) {
    byId('receipt-review').classList.remove('hidden');
    pending.items.forEach(addLine);
    byId('receipt-date').value = pending.purchase_date || byId('receipt-date').value;
    byId('receipt-text').value = pending.raw_text || '';
    byId('receipt-store').value = pending.store;
    byId('receipt-total').value = pending.total;
    byId('receipt-vat').value = pending.vat_amount ?? '';
    byId('receipt-vat-included').checked = pending.vat_included !== false;
    byId('receipt-adjustment').value = pending.adjustment_note;
    status.textContent = 'Hay un ticket pendiente de confirmación. Tocá confirmar para reintentar el mismo envío.';
  }
}
