/**
 * Expensa House - Frontend Application Logic
 * Sincronización en tiempo real, Búsqueda por Voz a Texto (Speech to Text),
 * Motor de Comparación de Ofertas con IA y Asistente Boti House.
 */

// Estado Global de la Aplicación
const state = {
  stock: [],
  shopping: [],
  budget: { monthlyBudget: 0, totalSpent: 0 },
  expenses: [],
  expenseMonth: new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires', year:'numeric', month:'2-digit', day:'2-digit'}).format(new Date()).slice(0, 7),
  activeTab: 'comparator',
  speechRecognition: null,
  isRecordingVoice: false,
  filterCategory: 'all',
  filterQuery: '',
  filterCriticalOnly: false
};

// ==========================================================================
// INICIALIZACIÓN
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => bootAuthentication(() => {
  initTheme();
  initNavigation();
  initSpeechRecognition();
  initEventListeners();
  loadAllData().then(() => {
    // Comparación inicial por defecto para impresionar al usuario
    if (window.currentUser.role !== 'inventory_viewer') performAIComparison("leche entera");
    else switchTab('stock');
  });
  setupMembers();
}));

// ==========================================================================
// TEMA CLARO / OSCURO
// ==========================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('expensa_theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    document.getElementById('btn-theme-toggle').textContent = '☀️';
  }

  document.getElementById('btn-theme-toggle').addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark-theme');
    localStorage.setItem('expensa_theme', isDark ? 'dark' : 'light');
    document.getElementById('btn-theme-toggle').textContent = isDark ? '☀️' : '🌙';
  });
}

// ==========================================================================
// NAVEGACIÓN ENTRE PESTAÑAS (TABS)
// ==========================================================================
function initNavigation() {
  const navButtons = document.querySelectorAll('.nav-btn');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll('.nav-btn').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-tab') === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });
}

// ==========================================================================
// CARGA Y SINCRONIZACIÓN DE DATOS CON FASTAPI
// ==========================================================================
let dataLoadSerial = 0;
async function loadAllData() {
  const serial = ++dataLoadSerial;
  try {
    const [stockRes, shopRes, budgetRes, expRes] = await Promise.all([
      fetch('/api/stock'),
      fetch('/api/shopping'),
      window.currentUser?.role === 'inventory_viewer' ? Promise.resolve({json: async () => ({monthlyBudget:0,totalSpent:0})}) : fetch(`/api/budget?month=${encodeURIComponent(state.expenseMonth)}`),
      window.currentUser?.role === 'inventory_viewer' ? Promise.resolve({json: async () => []}) : fetch('/api/expenses')
    ]);

    const responses = [stockRes, shopRes, budgetRes, expRes];
    const values = await Promise.all(responses.map(response => response.json()));
    if (serial !== dataLoadSerial) return;
    const failed = responses.findIndex(response => response.ok === false);
    if (failed >= 0) throw new Error(values[failed].detail || 'No se pudieron consultar los datos.');
    [state.stock, state.shopping, state.budget, state.expenses] = values;
    document.getElementById('expense-month-status').textContent = '';

    updateUI();
    showSyncIndicator(true);
  } catch (error) {
    if (serial !== dataLoadSerial) return;
    document.getElementById('expense-month-status').textContent = error.message;
    console.error('Error cargando datos del servidor:', error);
    showToast('⚠️ Error al sincronizar con el servidor.');
    showSyncIndicator(false);
  }
}

function showSyncIndicator(isOk) {
  const dot = document.querySelector('.sync-dot');
  const text = document.querySelector('.sync-text');
  if (isOk) {
    dot.style.backgroundColor = 'var(--color-leaf)';
    text.textContent = 'Sincronizado';
  } else {
    dot.style.backgroundColor = 'var(--color-coral)';
    text.textContent = 'Sin conexión';
  }
}

function updateUI() {
  renderDashboard();
  renderStockTable();
  renderShoppingList();
  renderBudgetAndExpenses();
  renderCriticalChips();
  updateBadgeCounts();
}

function updateBadgeCounts() {
  const shopCount = state.shopping.filter(s => !s.checked).length;
  const badge = document.getElementById('shopping-badge-count');
  badge.textContent = shopCount;
  badge.style.display = shopCount > 0 ? 'inline-block' : 'none';
}

// ==========================================================================
// BUSCADOR CON RECONOCIMIENTO DE VOZ (SPEECH-TO-TEXT)
// ==========================================================================
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const voiceBtn = document.getElementById('btn-voice-search');
  const statusBar = document.getElementById('voice-status-bar');
  const statusText = document.getElementById('voice-status-text');
  const searchInput = document.getElementById('ai-search-input');

  if (!SpeechRecognition) {
    console.warn('Web Speech API no está soportada de forma nativa en este navegador.');
    voiceBtn.title = 'Reconocimiento de voz no soportado en este navegador';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'es-AR';
  recognition.interimResults = true;
  recognition.continuous = false;

  recognition.onstart = () => {
    state.isRecordingVoice = true;
    voiceBtn.classList.add('recording');
    statusBar.classList.remove('hidden');
    statusText.textContent = '🎙️ Escuchando... Di algo como "Buscar ofertas de leche" o "Arroz"';
  };

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(result => result[0])
      .map(result => result.transcript)
      .join('');

    searchInput.value = transcript;
    statusText.textContent = `🗣️ "${transcript}"`;
  };

  recognition.onerror = (event) => {
    console.error('Error en reconocimiento de voz:', event.error);
    stopRecording();
    if (event.error === 'not-allowed') {
      showToast('⚠️ Permiso de micrófono denegado en el navegador.');
    } else {
      showToast('⚠️ No se pudo reconocer el audio. Intenta de nuevo.');
    }
  };

  recognition.onend = () => {
    stopRecording();
    const query = searchInput.value.trim();
    if (query) {
      showToast(`🔍 Buscando ofertas por voz: "${query}"`);
      performAIComparison(query);
    }
  };

  function startRecording() {
    try {
      recognition.start();
    } catch (e) {
      console.warn('Ya estaba grabando o reiniciando:', e);
    }
  }

  function stopRecording() {
    state.isRecordingVoice = false;
    voiceBtn.classList.remove('recording');
    statusBar.classList.add('hidden');
    try {
      recognition.stop();
    } catch (e) {}
  }

  voiceBtn.addEventListener('click', () => {
    if (state.isRecordingVoice) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  document.getElementById('btn-stop-voice').addEventListener('click', stopRecording);
}

// ==========================================================================
// COMPARADOR DE OFERTAS CON IA
// ==========================================================================
function escapeQuotes(str) {
  return (str || '').replace(/'/g, "\\'");
}

async function addOfferToShopping(name, brand, category, store) {
  try {
    const res = await fetch('/api/shopping', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        brand,
        category: category || 'Comestibles',
        detail: `Agregado desde oferta de ${store}`,
        quantity: 1,
        suggestedStore: store,
        checked: false
      })
    });
    const result = await res.json();
    state.shopping.push(result.item);
    updateUI();
    showToast(`✅ "${name}" agregado a tu Lista del Súper con ${store}.`);
  } catch (error) {
    console.error('Error agregando a lista:', error);
    showToast('⚠️ Error al agregar producto a la lista.');
  }
}

// Chips de acceso rápido basados en productos críticos
function renderCriticalChips() {
  const container = document.getElementById('critical-quick-chips');
  const criticalItems = state.stock.filter(s => s.stockQuantity <= 1);

  if (criticalItems.length === 0) return;

  container.innerHTML = '';
  criticalItems.slice(0, 6).forEach(item => {
    const btn = document.createElement('button');
    btn.className = 'chip';
    btn.textContent = `⚠️ ${item.name}`;
    btn.addEventListener('click', () => {
      performAIComparison(item.name);
    });
    container.appendChild(btn);
  });
}

// ==========================================================================
// DASHBOARD (KPIs & VISUALIZACIONES)
// ==========================================================================
function renderDashboard() {
  const totalUnits = state.stock.reduce((acc, s) => acc + (s.stockQuantity || 0) + (s.inUseCount || 0), 0);
  const criticalCount = state.stock.filter(s => s.stockQuantity <= 1).length;
  const distinctCount = state.stock.length;

  const budget = state.budget.monthlyBudget || 0;
  const spent = state.budget.totalSpent || 0;
  const remaining = Math.max(0, budget - spent);

  document.getElementById('kpi-total-units').textContent = totalUnits;
  document.getElementById('kpi-distinct-prods').textContent = `${distinctCount} productos distintos`;
  document.getElementById('kpi-critical-count').textContent = criticalCount;
  document.getElementById('kpi-remaining-budget').textContent = `$${remaining.toLocaleString('es-AR')}`;
  document.getElementById('kpi-spent-budget').textContent = `Gastado: $${spent.toLocaleString('es-AR')}`;

  // Barras de distribución por categoría
  const catDistribution = {};
  state.stock.forEach(s => {
    const cat = s.category || 'Otros';
    const total = (s.stockQuantity || 0) + (s.inUseCount || 0);
    catDistribution[cat] = (catDistribution[cat] || 0) + total;
  });

  const barsContainer = document.getElementById('category-distribution-bars');
  barsContainer.innerHTML = '';
  const maxVal = Math.max(...Object.values(catDistribution), 1);

  Object.entries(catDistribution).forEach(([cat, val]) => {
    const pct = Math.round((val / maxVal) * 100);
    const row = document.createElement('div');
    row.className = 'category-bar-row';
    row.innerHTML = `
      <div class="cat-bar-header">
        <span>${escapeHtml(cat)}</span>
        <span>${Number(val)} unidades</span>
      </div>
      <div class="cat-bar-bg">
        <div class="cat-bar-fill" style="width: ${pct}%;"></div>
      </div>
    `;
    barsContainer.appendChild(row);
  });

  // Lista de críticos en el dashboard
  const critList = document.getElementById('dashboard-critical-list');
  critList.innerHTML = '';
  const criticals = state.stock.filter(s => s.stockQuantity <= 1);

  if (criticals.length === 0) {
    critList.innerHTML = '<p class="text-subtle" style="font-size:0.9rem;">🎉 Todo en orden. No hay stock crítico en casa.</p>';
  } else {
    criticals.slice(0, 5).forEach(c => {
      const row = document.createElement('div');
      row.className = 'critical-item-row';
      row.innerHTML = `
        <div>
          <span class="critical-item-name">${escapeHtml(c.name)}</span>
          <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(c.brand)} • ${escapeHtml(c.category)}</div>
        </div>
        <div style="display:flex; align-items:center; gap:0.6rem;">
          <span class="critical-item-stock">${Number(c.stockQuantity)} cerradas</span>
          <button class="btn-sm-action" data-action="compare" data-query="${escapeHtml(c.name)}">
            🔍 Ofertas
          </button>
        </div>
      `;
      critList.appendChild(row);
    });
  }
}

// ==========================================================================
// INVENTARIO / TABLA DE STOCK
// ==========================================================================
function renderStockTable() {
  const tbody = document.getElementById('stock-table-body');
  tbody.innerHTML = '';

  let filtered = state.stock;

  // Filtro por categoría
  if (state.filterCategory !== 'all') {
    filtered = filtered.filter(s => s.category === state.filterCategory);
  }

  // Filtro por texto
  if (state.filterQuery) {
    const q = state.filterQuery.toLowerCase();
    filtered = filtered.filter(s => s.name.toLowerCase().includes(q) || (s.brand || '').toLowerCase().includes(q));
  }

  // Solo críticos
  if (state.filterCriticalOnly) {
    filtered = filtered.filter(s => s.stockQuantity <= 1);
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
          No se encontraron productos con los filtros seleccionados.
        </td>
      </tr>
    `;
    return;
  }

  filtered.forEach(item => {
    const isCritical = item.stockQuantity <= 1;
    const total = (item.stockQuantity || 0) + (item.inUseCount || 0);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <span class="table-prod-name">${escapeHtml(item.name)}</span>
        <span class="table-prod-brand">${escapeHtml(item.brand || 'Genérica')} • ${escapeHtml(item.unit || 'unidad')}</span>
      </td>
      <td>
        <span class="cat-badge">${escapeHtml(item.category)}</span>
      </td>
      <td class="text-center">
        <div class="qty-control-wrapper">
          <button class="btn-qty" data-action="stock-minus" data-id="${escapeHtml(item.id)}">-</button>
          <span class="qty-num">${Number(item.stockQuantity)}</span>
          <button class="btn-qty" data-action="stock-plus" data-id="${escapeHtml(item.id)}">+</button>
        </div>
      </td>
      <td class="text-center">
        <div class="qty-control-wrapper">
          <button class="btn-qty" data-action="consume" data-id="${escapeHtml(item.id)}" title="Terminar / Consumir">-</button>
          <span class="qty-num" style="color:var(--color-amber);">${Number(item.inUseCount)}</span>
          <button class="btn-qty" data-action="open" data-id="${escapeHtml(item.id)}" title="Abrir una unidad cerrada">+</button>
        </div>
      </td>
      <td class="text-center">
        <span class="total-qty-pill">${Number(total)}</span>
      </td>
      <td>
        <span class="status-badge ${isCritical ? 'critical' : 'available'}">
          ${isCritical ? '⚠️ Crítico' : '✅ Disponible'}
        </span>
      </td>
      <td class="text-right">
        <div class="table-actions">
          <button class="btn-sm-action open-unit" data-action="open" data-id="${escapeHtml(item.id)}" title="Pasa 1 unidad de stock cerrado a abierto">
            🔓 Abrir
          </button>
          <button class="btn-sm-action" data-action="compare" data-query="${escapeHtml(item.name)}" title="Comparar precios en supermercados">
            🛒 IA Ofertas
          </button>
          <button class="btn-sm-action" data-action="edit" data-id="${escapeHtml(item.id)}">✏️</button>
          <button class="btn-sm-action delete" data-action="delete-stock" data-id="${escapeHtml(item.id)}">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function changeStockQuantity(id, delta) {
  const item = state.stock.find(s => s.id === id);
  if (!item) return;

  const newQty = Math.max(0, (item.stockQuantity || 0) + delta);
  try {
    const res = await fetch(`/api/stock/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...item, stockQuantity: newQty })
    });
    const result = await res.json();
    item.stockQuantity = newQty;
    updateUI();
  } catch (e) {
    showToast('⚠️ Error al actualizar stock.');
  }
}

async function changeInUseQuantity(id, delta) {
  const item = state.stock.find(s => s.id === id);
  if (!item) return;

  if (delta < 0) {
    // Consumir unidad abierta
    try {
      const res = await fetch(`/api/stock/${id}/consume`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        item.inUseCount = data.item.inUseCount;
        updateUI();
        showToast(`🥣 Unidad consumida de "${item.name}".`);
      }
    } catch (e) {}
  } else {
    // Abrir unidad
    openStockUnit(id);
  }
}

async function openStockUnit(id) {
  const item = state.stock.find(s => s.id === id);
  if (!item || item.stockQuantity <= 0) {
    showToast('⚠️ No tienes unidades cerradas en stock para abrir.');
    return;
  }
  try {
    const res = await fetch(`/api/stock/${id}/open`, { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      item.stockQuantity = data.item.stockQuantity;
      item.inUseCount = data.item.inUseCount;
      updateUI();
      showToast(`🔓 Se abrió una unidad de "${item.name}".`);
    }
  } catch (e) {
    showToast('⚠️ Error al abrir unidad.');
  }
}

async function deleteStockItem(id) {
  if (!confirm('¿Seguro que deseas eliminar este producto del inventario?')) return;
  try {
    await fetch(`/api/stock/${id}`, { method: 'DELETE' });
    state.stock = state.stock.filter(s => s.id !== id);
    updateUI();
    showToast('🗑️ Producto eliminado.');
  } catch (e) {
    showToast('⚠️ Error al eliminar.');
  }
}

// ==========================================================================
// LISTA DEL SÚPER (SHOPPING LIST)
// ==========================================================================
function renderShoppingList() {
  const container = document.getElementById('shopping-list-container');
  container.innerHTML = '';

  if (state.shopping.length === 0) {
    container.innerHTML = `
      <div class="card-panel" style="text-align:center; padding:3rem;">
        <span style="font-size:3rem;">🛒</span>
        <h3 style="margin-top:1rem;">Tu lista de compras está vacía</h3>
        <p style="color:var(--text-muted); font-size:0.95rem;">Los productos en stock crítico se agregarán aquí automáticamente, o puedes agregarlos desde el comparador de ofertas.</p>
      </div>
    `;
    return;
  }

  // Agrupar por categoría
  const groups = {};
  state.shopping.forEach(item => {
    const cat = item.category || 'General';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(item);
  });

  Object.entries(groups).forEach(([category, items]) => {
    const groupCard = document.createElement('div');
    groupCard.className = 'shopping-group';

    const header = document.createElement('div');
    header.className = 'shopping-group-header';
    header.innerHTML = `
      <span>${escapeHtml(category)}</span>
      <span style="font-size:0.8rem; font-weight:700; color:var(--text-muted);">${items.length} ítems</span>
    `;
    groupCard.appendChild(header);

    const itemsGrid = document.createElement('div');
    itemsGrid.className = 'shopping-items-grid';

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = `shopping-item-card ${item.checked ? 'checked' : ''}`;

      card.innerHTML = `
        <div class="shopping-left-col">
          <input type="checkbox" class="custom-checkbox" ${item.checked ? 'checked' : ''} data-action="toggle-shopping" data-id="${escapeHtml(item.id)}">
          <div class="shop-item-info ${item.checked ? 'checked' : ''}">
            <h4>${escapeHtml(item.name)}</h4>
            <div class="shop-item-sub">
              ${escapeHtml(item.brand || 'Genérica')} • Cantidad: <strong>${Number(item.quantity) || 1}</strong>
              ${item.suggestedStore ? `<span class="shop-suggested-store">📍 ${escapeHtml(item.suggestedStore)}</span>` : ''}
            </div>
            ${item.detail ? `<div style="font-size:0.75rem; color:var(--text-subtle); margin-top:2px;">${escapeHtml(item.detail)}</div>` : ''}
          </div>
        </div>

        <div class="shopping-right-actions">
          <button class="btn-move-stock" data-action="move-stock" data-id="${escapeHtml(item.id)}" title="Pasa este ítem directamente a tu alacena">
            ✅ A Stock
          </button>
          <button class="btn-sm-action delete" data-action="delete-shopping" data-id="${escapeHtml(item.id)}">🗑️</button>
        </div>
      `;
      itemsGrid.appendChild(card);
    });

    groupCard.appendChild(itemsGrid);
    container.appendChild(groupCard);
  });
}

async function toggleShoppingItem(id) {
  try {
    const res = await fetch(`/api/shopping/${id}/toggle`, { method: 'POST' });
    const result = await res.json();
    const item = state.shopping.find(s => s.id === id);
    if (item) item.checked = result.item.checked;
    updateUI();
  } catch (e) {}
}

async function moveShoppingToStock(id) {
  try {
    const res = await fetch(`/api/shopping/${id}/move-to-stock`, { method: 'POST' });
    const result = await res.json();
    state.shopping = state.shopping.filter(s => s.id !== id);
    
    // Actualizar o insertar en stock local
    const existing = state.stock.find(s => s.id === result.stock_item.id);
    if (existing) {
      existing.stockQuantity = result.stock_item.stockQuantity;
    } else {
      state.stock.push(result.stock_item);
    }

    updateUI();
    showToast(`📦 "${result.stock_item.name}" transferido a tu alacena.`);
  } catch (e) {
    showToast('⚠️ Error al mover producto a stock.');
  }
}

async function deleteShoppingItem(id) {
  try {
    await fetch(`/api/shopping/${id}`, { method: 'DELETE' });
    state.shopping = state.shopping.filter(s => s.id !== id);
    updateUI();
  } catch (e) {}
}

// ==========================================================================
// PRESUPUESTO & GASTOS
// ==========================================================================
// ==========================================================================
// MODALES DE FORMULARIO
// ==========================================================================
function initEventListeners() {
  const monthInput = document.getElementById('expense-month');
  monthInput.value = state.expenseMonth;
  monthInput.addEventListener('change', async () => {
    if (!monthInput.value) return;
    state.expenseMonth = monthInput.value;
    await loadAllData();
  });
  // Buscador principal
  const searchInput = document.getElementById('ai-search-input');
  const searchBtn = document.getElementById('btn-ai-search');

  searchBtn.addEventListener('click', () => {
    performAIComparison(searchInput.value.trim());
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      performAIComparison(searchInput.value.trim());
    }
  });

  // Filtros de stock
  document.getElementById('stock-filter-query').addEventListener('input', (e) => {
    state.filterQuery = e.target.value;
    renderStockTable();
  });

  document.getElementById('stock-filter-critical-only').addEventListener('change', (e) => {
    state.filterCriticalOnly = e.target.checked;
    renderStockTable();
  });

  document.querySelectorAll('#stock-category-filters .filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('#stock-category-filters .filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.filterCategory = chip.getAttribute('data-cat');
      renderStockTable();
    });
  });

  // Forzar Sincronización
  document.getElementById('btn-sync-now').addEventListener('click', async () => {
    showToast('🔄 Sincronizando con el servidor...');
    await loadAllData();
    showToast('✅ Sincronización completada.');
  });

  // Modales Open / Close
  setupModalTriggers();

  // Form Submits
  setupFormSubmits();

  // Boti House Chat
  setupBotiHouseChat();
  setupReceiptScanner();
  setupSavedOffers();
  document.getElementById("offer-sort").addEventListener("change", () => performAIComparison(searchInput.value));
  if (location.hash === "receipts") switchTab("budget");
}

function setupModalTriggers() {
  // Modal Stock
  document.getElementById('btn-open-add-stock-modal').addEventListener('click', () => {
    document.getElementById('form-stock').reset();
    document.getElementById('stock-form-id').value = '';
    document.getElementById('modal-stock-title').textContent = 'Agregar Producto a la Alacena';
    openModal('modal-stock');
  });

  // Modal Shopping
  document.getElementById('btn-open-add-shopping-modal').addEventListener('click', () => {
    document.getElementById('form-shopping').reset();
    openModal('modal-shopping');
  });

  // Modal Budget
  document.getElementById('btn-open-budget-modal').addEventListener('click', () => {
    document.getElementById('budget-form-amount').value = state.budget.monthlyBudget || '';
    openModal('modal-budget');
  });

  // Modal Expense
  document.getElementById('btn-open-expense-modal').addEventListener('click', () => {
    document.getElementById('form-expense').reset();
    openModal('modal-expense');
  });

  // Close buttons
  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close');
      closeModal(modalId);
    });
  });
}

function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}

function openEditStockModal(id) {
  const item = state.stock.find(s => s.id === id);
  if (!item) return;

  document.getElementById('stock-form-id').value = item.id;
  document.getElementById('stock-form-name').value = item.name;
  document.getElementById('stock-form-brand').value = item.brand || '';
  document.getElementById('stock-form-category').value = item.category || 'Comestibles';
  document.getElementById('stock-form-qty').value = item.stockQuantity || 0;
  document.getElementById('stock-form-inuse').value = item.inUseCount || 0;
  document.getElementById('stock-form-unit').value = item.unit || 'unidad';
  document.getElementById('stock-form-price').value = item.price || '';

  document.getElementById('modal-stock-title').textContent = 'Editar Producto';
  openModal('modal-stock');
}

function setupFormSubmits() {
  // Guardar Stock
  document.getElementById('form-stock').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('stock-form-id').value;
    const payload = {
      name: document.getElementById('stock-form-name').value.trim(),
      brand: document.getElementById('stock-form-brand').value.trim() || 'Genérica',
      category: document.getElementById('stock-form-category').value,
      stockQuantity: parseInt(document.getElementById('stock-form-qty').value) || 0,
      inUseCount: parseInt(document.getElementById('stock-form-inuse').value) || 0,
      unit: document.getElementById('stock-form-unit').value.trim() || 'unidad',
      price: parseFloat(document.getElementById('stock-form-price').value) || 0
    };

    try {
      const url = id ? `/api/stock/${id}` : '/api/stock';
      const method = id ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (id) {
        const idx = state.stock.findIndex(s => s.id === id);
        if (idx !== -1) state.stock[idx] = data.item;
      } else {
        state.stock.push(data.item);
      }

      closeModal('modal-stock');
      updateUI();
      showToast('✅ Producto guardado en el inventario.');
    } catch (err) {
      showToast('⚠️ Error al guardar producto.');
    }
  });

  // Guardar Shopping
  document.getElementById('form-shopping').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('shop-form-name').value.trim(),
      brand: document.getElementById('shop-form-brand').value.trim() || 'Genérica',
      category: document.getElementById('shop-form-category').value,
      quantity: parseInt(document.getElementById('shop-form-qty').value) || 1,
      suggestedStore: document.getElementById('shop-form-store').value || null,
      detail: document.getElementById('shop-form-detail').value.trim() || 'Agregado manual',
      checked: false
    };

    try {
      const res = await fetch('/api/shopping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      state.shopping.push(data.item);
      closeModal('modal-shopping');
      updateUI();
      showToast('✅ Producto agregado a la lista del súper.');
    } catch (err) {
      showToast('⚠️ Error al agregar producto.');
    }
  });

  // Guardar Presupuesto
  document.getElementById('form-budget').addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = parseFloat(document.getElementById('budget-form-amount').value) || 0;

    try {
      const res = await fetch('/api/budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monthlyBudget: amount })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo guardar el presupuesto.");
      await loadAllData();
      closeModal('modal-budget');
      updateUI();
      showToast('💰 Presupuesto mensual actualizado.');
    } catch (err) {
      showToast('⚠️ Error al guardar presupuesto.');
    }
  });

  // Guardar Ticket / Gasto
  document.getElementById('form-expense').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      amount: parseFloat(document.getElementById('expense-form-amount').value) || 0,
      category: document.getElementById('expense-form-category').value,
      note: document.getElementById('expense-form-note').value.trim() || 'Compra de súper'
    };

    try {
      const res = await fetch('/api/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo registrar el gasto.");
      await loadAllData();
      closeModal('modal-expense');
      updateUI();
      showToast('🧾 Ticket registrado con éxito.');
    } catch (err) {
      showToast('⚠️ Error al registrar ticket.');
    }
  });
}

// ==========================================================================
// ASISTENTE BOTI HOUSE (CHATBOT IA)
// ==========================================================================
// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================
function showToast(msg) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}


// No inline JavaScript: CSP blocks event-handler injection from product descriptions.
document.addEventListener('click', event => {
  const target = event.target.closest('[data-action]');
  if (!target || target.matches('input[type=checkbox]')) return;
  const id = target.dataset.id;
  if (target.dataset.action === 'compare') {
    if (window.currentUser?.role !== 'inventory_viewer') { performAIComparison(target.dataset.query); switchTab('comparator'); }
    return;
  }
  if (!canEditHousehold()) return;
  const actions = {'stock-minus':()=>changeStockQuantity(id,-1),'stock-plus':()=>changeStockQuantity(id,1),
    consume:()=>changeInUseQuantity(id,-1),open:()=>openStockUnit(id),edit:()=>openEditStockModal(id),
    'delete-stock':()=>deleteStockItem(id),'move-stock':()=>moveShoppingToStock(id),'delete-shopping':()=>deleteShoppingItem(id)};
  actions[target.dataset.action]?.();
});
document.addEventListener('change', event => {
  if (event.target.dataset.action === 'toggle-shopping' && canEditHousehold()) toggleShoppingItem(event.target.dataset.id);
});
