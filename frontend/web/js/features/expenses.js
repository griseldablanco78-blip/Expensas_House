// Monthly expense view and private receipt downloads.
function renderBudgetAndExpenses() {
  renderOfferReceiptHistory();
  const budget = state.budget.monthlyBudget || 0;
  const spent = state.budget.totalSpent || 0;
  const remaining = budget - spent;
  const pct = budget > 0 ? Math.min(100, Math.round((spent / budget) * 100)) : 0;

  document.getElementById('budget-total-display').textContent = `$${budget.toLocaleString('es-AR')}`;

  const remainingDisplay = document.getElementById('budget-remaining-display');
  remainingDisplay.textContent = `$${remaining.toLocaleString('es-AR')}`;
  remainingDisplay.style.color = remaining < 0 ? 'var(--color-coral)' : 'var(--color-leaf)';

  const progressBar = document.getElementById('budget-progress-bar');
  progressBar.style.width = `${pct}%`;
  progressBar.className = `progress-bar-fill ${pct > 90 ? 'warning' : ''}`;

  document.getElementById('budget-spent-text').textContent = `Total gastado: $${spent.toLocaleString('es-AR')}`;
  document.getElementById('budget-percent-text').textContent = `${pct}% utilizado`;

  // Tabla de gastos
  const expTbody = document.getElementById('expenses-table-body');
  expTbody.innerHTML = '';

  const expenses = state.expenses.filter(e => (e.purchase_date || (e.timestamp ? new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires', year:'numeric', month:'2-digit', day:'2-digit'}).format(new Date(e.timestamp)) : '')).startsWith(state.expenseMonth));
  document.getElementById('expense-store-summary').textContent = (state.budget.by_store || []).map(group => `${group.store}: $${group.amount.toLocaleString('es-AR')}`).join(' · ') || 'Sin gastos para este mes.';
  const products = document.getElementById('expense-products-body');
  products.replaceChildren();
  const dateFilter = document.getElementById('expense-receipt-date');
  const selected = dateFilter.value;
  const dates = [...new Set(expenses.filter(e => e.items?.length).map(e => e.purchase_date || (e.timestamp ? new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires', year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(e.timestamp)) : '')).filter(Boolean))].sort().reverse();
  dateFilter.replaceChildren(new Option('Todas las compras del mes', ''));
  dates.forEach(date => dateFilter.add(new Option(date, date)));
  dateFilter.value = dates.includes(selected) ? selected : '';
  dateFilter.onchange = renderBudgetAndExpenses;
  expenses.filter(e => !dateFilter.value || (e.purchase_date || (e.timestamp ? new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(e.timestamp)) : '')) === dateFilter.value).forEach(expense => (expense.items || []).forEach(item => {
    const row = document.createElement('tr');
    const currency = value => '$' + Number(value || 0).toLocaleString('es-AR', {minimumFractionDigits:2, maximumFractionDigits:2});
    [expense.purchase_date || (expense.timestamp ? new Date(expense.timestamp).toLocaleDateString('es-AR', {timeZone:'America/Argentina/Buenos_Aires'}) : 'Sin fecha'), expense.store || expense.note || 'Sin supermercado', item.description, item.quantity,
      currency(item.unit_price), currency(item.line_total)].forEach(value => {
        const cell = row.insertCell(); cell.textContent = String(value);
      });
    products.appendChild(row);
  }));
  if (!products.children.length) {
    const cell = products.insertRow().insertCell(); cell.colSpan = 7; cell.textContent = 'Sin productos detallados en este mes.';
  }
  if (expenses.length === 0) {
    expTbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1.5rem; color:var(--text-muted);">Aún no hay tickets registrados.</td></tr>';
    return;
  }

  expenses.forEach(e => {
    const dateStr = e.purchase_date ? new Date(e.purchase_date + 'T12:00:00-03:00').toLocaleDateString('es-AR') : e.timestamp ? new Date(e.timestamp).toLocaleDateString('es-AR') : 'Reciente';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${dateStr}</td>
      <td><span class="cat-badge">${escapeHtml(e.category)}</span></td>
      <td>${escapeHtml(e.store || e.note || '-')} ${(e.items || []).length ? `<details><summary>Ver ${e.items.length} productos</summary>${e.items.map(i => `${escapeHtml(i.description)} · ${Number(i.quantity)} × $${Number(i.unit_price)} = $${Number(i.line_total)}`).join('<br>')}</details>` : ''} ${e.source === 'receipt' ? `<p><a href="/api/receipts/${encodeURIComponent(e.id)}/text" download>Descargar texto</a>${e.receipt_image ? ` · <a href="/api/receipts/${encodeURIComponent(e.id)}/image" target="_blank" rel="noopener">Ver comprobante</a>` : ''}</p>` : ''}</td>
      <td class="text-right" style="font-weight:800; font-family:var(--font-heading); color:var(--text-main);">$${(e.amount || 0).toLocaleString('es-AR')}</td>
    `;
    expTbody.appendChild(tr);
  });
}


let receiptPreviewUrl = null;
let receiptPreviewSerial = 0;
function renderOfferReceiptHistory() {
  const list = document.getElementById('offer-receipt-list');
  list.replaceChildren();
  const dateOf = receipt => receipt.purchase_date || (receipt.timestamp ? new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(receipt.timestamp)) : 'Sin fecha');
  [...state.expenses].sort((a,b) => dateOf(b).localeCompare(dateOf(a))).forEach(receipt => {
    const button = document.createElement('div');
    button.className = 'saved-receipt-row';
    const open = document.createElement('button'); open.type = 'button'; open.className = 'saved-receipt-open';
    const date = document.createElement('span'); date.textContent = dateOf(receipt);
    const store = document.createElement('strong'); store.textContent = receipt.store || receipt.note || 'Comercio sin nombre';
    open.append(date, store); button.append(open);
    if (canEditHousehold()) {
      const trash = document.createElement('button'); trash.type = 'button'; trash.className = 'receipt-delete-button';
      trash.textContent = '🗑'; trash.setAttribute('aria-label', 'Eliminar ticket de ' + store.textContent);
      trash.addEventListener('click', event => { event.stopPropagation(); deleteSavedReceipt(receipt, trash); });
      trash.addEventListener('dblclick', event => event.stopPropagation());
      trash.addEventListener('touchend', event => event.stopPropagation());
      button.append(trash);
    }
    button.title = 'Doble clic para abrir el ticket';
    button.addEventListener('dblclick', () => openSavedReceipt(receipt));
    button.addEventListener('keydown', event => { if (event.target === open && event.key === 'Enter') { event.preventDefault(); openSavedReceipt(receipt); } });
    // Touch double-tap on browsers that do not synthesize dblclick.
    let previousTap = 0;
    button.addEventListener('touchend', event => {
      const now = Date.now();
      if (previousTap && now - previousTap < 350) { event.preventDefault(); openSavedReceipt(receipt); previousTap = 0; }
      else previousTap = now;
    });
    list.appendChild(button);
  });
  if (!list.children.length) list.textContent = 'Todavía no hay tickets guardados.';
}

async function openSavedReceipt(receipt) {
  const dialog = document.getElementById('saved-receipt-dialog');
  if (dialog.open) return;
  const serial = ++receiptPreviewSerial;
  const content = document.getElementById('saved-receipt-content'); content.replaceChildren();
  document.getElementById('saved-receipt-title').textContent = receipt.store || receipt.note || 'Ticket guardado';
  const date = document.createElement('p'); date.textContent = receipt.purchase_date || 'Sin fecha de compra'; content.append(date);
  const total = document.createElement('p'); total.textContent = 'Descontado del presupuesto: $' + Number(receipt.amount).toLocaleString('es-AR'); content.append(total);
  (receipt.items || []).forEach(item => {
    const row = document.createElement('p');
    row.textContent = `${item.description} · ${item.quantity} × $${Number(item.unit_price).toLocaleString('es-AR')} = $${Number(item.line_total).toLocaleString('es-AR')}`;
    content.append(row);
  });
  const status = document.createElement('p'); status.textContent = 'Cargando imagen del ticket…'; content.append(status);
  const close = () => {
    receiptPreviewSerial++;
    if (receiptPreviewUrl) { URL.revokeObjectURL(receiptPreviewUrl); receiptPreviewUrl = null; }
  };
  dialog.onclose = close;
  document.getElementById('saved-receipt-close').onclick = () => dialog.close();
  dialog.showModal();
  try {
    const response = await fetch(`/api/receipts/${encodeURIComponent(receipt.id)}/image`);
    if (!response.ok) throw new Error('Imagen no disponible');
    const photo = await response.blob();
    if (!dialog.open || serial !== receiptPreviewSerial) return;
    receiptPreviewUrl = URL.createObjectURL(photo);
    const image = document.createElement('img'); image.src = receiptPreviewUrl; image.alt = 'Imagen del ticket guardado'; image.className = 'saved-receipt-photo';
    status.replaceWith(image);
  } catch {
    if (dialog.open && serial === receiptPreviewSerial) status.textContent = 'No hay una imagen disponible para este gasto. Los productos guardados se muestran arriba.';
  }
}


async function deleteSavedReceipt(receipt, button) {
  const store = receipt.store || receipt.note || 'este comercio';
  if (!window.confirm(`¿Eliminar el ticket de ${store} del ${receipt.purchase_date || 'día registrado'}? Se quitarán $${Number(receipt.amount).toLocaleString('es-AR')} del gasto registrado y se actualizará el presupuesto disponible.`)) return;
  button.disabled = true;
  try {
    const response = await fetch(`/api/receipts/${encodeURIComponent(receipt.id)}`, {method:'DELETE'});
    const result = await readApiJson(response);
    if (!response.ok) throw new Error(result.detail || 'No se pudo eliminar el ticket.');
    state.expenses = state.expenses.filter(row => row.id !== receipt.id);
    renderOfferReceiptHistory();
    await loadAllData();
    showToast('Ticket eliminado. Presupuesto actualizado.');
  } catch (error) { button.disabled = false; showToast(error.message); }
}
