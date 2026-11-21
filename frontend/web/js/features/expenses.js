// Monthly expense view and private receipt downloads.
function renderBudgetAndExpenses() {
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
      <td>${escapeHtml(e.store || e.note || '-')} ${(e.items || []).length ? `<details><summary>Ver ${e.items.length} productos</summary>${e.items.map(i => `${escapeHtml(i.description)} · ${Number(i.quantity)} × $${Number(i.unit_price)} = $${Number(i.line_total)}`).join('<br>')}</details>` : ''} ${e.source === 'receipt' ? `<p>IVA: ${e.vat_amount == null ? 'No informado' : '$' + Number(e.vat_amount).toLocaleString('es-AR')} (${e.vat_included === false ? 'separado' : 'incluido'})</p><p><a href="/api/receipts/${encodeURIComponent(e.id)}/text" download>Descargar texto</a>${e.receipt_image ? ` · <a href="/api/receipts/${encodeURIComponent(e.id)}/image" target="_blank" rel="noopener">Ver comprobante</a>` : ''}</p>` : ''}</td>
      <td class="text-right" style="font-weight:800; font-family:var(--font-heading); color:var(--text-main);">$${(e.amount || 0).toLocaleString('es-AR')}</td>
    `;
    expTbody.appendChild(tr);
  });
}
