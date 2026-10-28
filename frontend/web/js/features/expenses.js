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

