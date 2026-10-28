function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
}
function safeUrl(value) { return (/^(?:https?:\/\/)/i.test(value || '') || /^\/api\/offers\/images\/[a-f0-9]{32}\.jpg$/.test(value || '')) ? value : ''; }
