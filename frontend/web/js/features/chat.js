function setupBotiHouseChat() {
  const toggleBtn = document.getElementById('boti-toggle-btn');
  const chatPanel = document.getElementById('boti-chat-panel');
  const closeBtn = document.getElementById('btn-close-boti');
  const input = document.getElementById('boti-user-input');
  const sendBtn = document.getElementById('btn-send-boti');
  const messagesBox = document.getElementById('boti-messages');

  toggleBtn.addEventListener('click', () => {
    chatPanel.classList.toggle('hidden');
    toggleBtn.setAttribute('aria-expanded', String(!chatPanel.classList.contains('hidden')));
    if (!chatPanel.classList.contains('hidden')) input.focus();
  });

  closeBtn.addEventListener('click', () => {
    chatPanel.classList.add('hidden');
    toggleBtn.setAttribute('aria-expanded', 'false'); toggleBtn.focus();
  });

  let chatContext = null;
  let sending = false;
  async function sendMessage(prompt) {
    const text = (typeof prompt === "string" ? prompt : input.value).trim();
    if (sending) return;
    if (!text) return;

    sending = true;
    sendBtn.disabled = true; toggleBtn.classList.add('is-thinking');
    const pending = document.createElement('div'); pending.className = 'boti-msg bot boti-thinking'; pending.textContent = 'Consultando tu hogar…'; messagesBox.appendChild(pending);
    // Agregar mensaje del usuario
    appendMessage(text, 'user');
    input.value = '';

    // Llamar al backend de IA
    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, context: chatContext })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'No se pudo consultar');
      chatContext = data.context || null;
      appendMessage(data.answer, 'bot');
      if (data.action) switchTab(data.action);
      if (data.comparison) { document.getElementById('ai-search-input').value = text; renderComparisonResults(data.comparison); }
    } catch (e) {
      appendMessage('No se pudo procesar la consulta. Intentá de nuevo.', 'bot');
    } finally { pending.remove(); sending = false; sendBtn.disabled = false; toggleBtn.classList.remove('is-thinking'); }
  }

  function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `boti-msg ${sender}`;
    div.textContent = text;
    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  sendBtn.addEventListener('click', () => sendMessage());
  document.querySelector('.boti-widget-container').addEventListener('click', event => { const button = event.target.closest('[data-chat-prompt]'); if (button) sendMessage(button.dataset.chatPrompt); });
  chatPanel.addEventListener('keydown', e => { if (e.key === 'Escape') closeBtn.click(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
}

