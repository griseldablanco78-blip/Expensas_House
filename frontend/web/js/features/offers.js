async function performAIComparison(query) {
  if (!query || !query.trim()) return;
  const serial = ++comparisonSerial;

  const loading = document.getElementById('comparator-loading');
  const resultsContainer = document.getElementById('comparator-results');
  const searchInput = document.getElementById('ai-search-input');

  searchInput.value = query;
  loading.classList.remove('hidden');
  resultsContainer.style.opacity = '0.3';

  try {
    const res = await fetch(`/api/offers/compare?q=${encodeURIComponent(query)}&sort=${document.getElementById('offer-sort').value}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "No se pudieron consultar las ofertas");
    if (serial === comparisonSerial) renderComparisonResults(data);
  } catch (error) {
    console.error('Error en la comparación IA:', error);
    if (serial === comparisonSerial) {
      document.getElementById('offer-source-status').textContent = error.message;
      document.getElementById('supermarket-cards-container').textContent = 'No se pudo completar la consulta. Reintentá la búsqueda.';
      showToast(error.message);
    }
  } finally {
    if (serial === comparisonSerial) { loading.classList.add('hidden'); resultsContainer.style.opacity = '1'; }
  }
}

let comparisonSerial = 0;
function renderComparisonResults(data) {
  const analysis = data.ai_analysis;
  const offers = data.offers || [];
  document.getElementById('comparison-target-title').textContent = `Ofertas para "${data.product_name}"`;
  document.getElementById('comparison-store-count').textContent = `${offers.length} ofertas`;
  document.getElementById('verdict-text').textContent = analysis.verdict;
  document.getElementById('offer-source-status').textContent = data.warning || '';
  document.getElementById('ratoneando-search').href = safeUrl(data.external_search_url) || 'https://ratoneando.ar/';
  document.getElementById('val-best-single').textContent = offers.length ? `${analysis.best_single.store} ($${analysis.best_single.price.toLocaleString('es-AR')})` : 'Sin ofertas';
  document.getElementById('val-best-bulk').textContent = data.top_offer ? data.top_offer.store : 'Sin ofertas';
  document.getElementById('val-max-saving').textContent = analysis.max_saving_percent > 0 ? `${analysis.max_saving_percent}% informado` : 'Sin descuento informado';
  const alert = document.getElementById('verdict-stock-alert');
  alert.textContent = analysis.stock_alert || '';
  alert.style.display = analysis.stock_alert ? 'block' : 'none';
  const container = document.getElementById('supermarket-cards-container');
  container.replaceChildren();
  if (!offers.length) container.textContent = 'No hay ofertas coincidentes. Podés consultar Ratoneando con el enlace de arriba.';
  offers.forEach((off, index) => {
    const card = document.createElement('div');
    card.className = `store-card ${index === 0 ? 'is-winner' : ''}`;
    const image = safeUrl(off.image_url);
    const link = safeUrl(off.direct_link);
    card.innerHTML = `
      ${index === 0 ? '<strong class="top-offer-label">🏆 Oferta top según el filtro elegido</strong>' : ''}
      <div class="product-image-slot">${image ? `<img class="offer-product-image" src="${escapeHtml(image)}" alt="${escapeHtml(off.product)}" loading="lazy" referrerpolicy="no-referrer">` : '<span class="product-photo-empty"><span aria-hidden="true">▧</span>Sin fotografía<small>Podés agregarla en Mis ofertas</small></span>'}</div>
      <h4 class="store-product-title">${escapeHtml(off.product)}</h4>
      <strong>${escapeHtml(off.store)}</strong>
      <span>${escapeHtml(off.brand)}</span>
      <p>${escapeHtml(off.promo_text)}</p>
      <p>${escapeHtml(off.conditions)}</p>
      <strong class="promo-price">$${off.promo_price.toLocaleString('es-AR')}</strong>
      <small>Fuente: ${escapeHtml(off.source)}${off.updated_at ? ` · ${escapeHtml(off.updated_at)}` : ' · Sin fecha informada'}</small>
      ${link ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">Ver oferta en el supermercado</a>` : ''}
      <button class="btn-add-to-cart">➕ A la lista</button>`;
    card.querySelector('img')?.addEventListener('error', event => {
      event.target.parentElement.textContent = '📦 Imagen no disponible';
    });
    card.querySelector('button').addEventListener('click', () => addOfferToShopping(off.product, off.brand, data.category, off.store));
    const photo = card.querySelector('img');
    if (photo) photo.addEventListener('error', () => { const fallback = document.createElement('span'); fallback.className = 'product-photo-empty'; fallback.textContent = 'La fotografía no está disponible'; photo.replaceWith(fallback); }, {once:true});
    container.appendChild(card);
  });
}



async function setupSavedOffers() {
  if (!canEditHousehold()) return;
  const form = document.getElementById('saved-offer-form');
  const select = document.getElementById('saved-offer-id');
  const status = document.getElementById('saved-offer-status');
  let offers = [];
  function selected() {
    const item = offers.find(o => o.id === select.value);
    document.getElementById('saved-offer-store').value = item?.store || '';
    document.getElementById('saved-offer-product').value = item?.product || '';
    const raw = String(item?.price || '').replace(/[$\s]/g, '');
    document.getElementById('saved-offer-price').value = /^\d+(\.\d+)?$/.test(raw) ? raw : '';
    document.getElementById('saved-offer-image').value = '';
  }
  async function refresh() {
    const res = await fetch('/api/offers/saved');
    if (!res.ok) { status.textContent = 'No se pudieron cargar las ofertas guardadas.'; return; }
    offers = await res.json(); select.replaceChildren();
    const fresh = document.createElement('option'); fresh.value = ''; fresh.textContent = '+ Agregar oferta'; select.appendChild(fresh);
    for (const offer of offers) {
      const option = document.createElement('option'); option.value = offer.id;
      option.textContent = `${offer.product} · ${offer.store}`; select.appendChild(option);
    }
    if (!offers.length) status.textContent = 'Todavía no hay ofertas guardadas. Cargá una desde la app y sincronizá.';
    selected();
  }
  select.addEventListener('change', selected);
  form.addEventListener('submit', async event => {
    event.preventDefault(); const button = form.querySelector('[type=submit]'); button.disabled = true;
    try {
      let id = encodeURIComponent(select.value);
      const response = await fetch(id ? `/api/offers/saved/${id}` : '/api/offers/saved', {method:id ? 'PATCH' : 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store:document.getElementById('saved-offer-store').value, product:document.getElementById('saved-offer-product').value, price:Number(document.getElementById('saved-offer-price').value)})});
      const result = await response.json(); if (!response.ok) throw new Error(result.detail || 'No se pudo guardar.');
      if (!id) id = encodeURIComponent(result.id);
      const photo = document.getElementById('saved-offer-image').files[0];
      if (photo) {
        const data = new FormData(); data.append('image', photo);
        const uploaded = await fetch(`/api/offers/saved/${id}/image`, {method:'POST', body:data});
        const info = await uploaded.json(); if (!uploaded.ok) throw new Error('Precio guardado. ' + (info.detail || 'No se pudo guardar la foto.'));
      }
      status.textContent = 'Oferta guardada. La búsqueda ya usa los datos actualizados.';
      await refresh(); const query = document.getElementById('ai-search-input').value; if (query) await performAIComparison(query);
    } catch (error) { status.textContent = error.message; } finally { button.disabled = false; }
  });
  await refresh();
}
