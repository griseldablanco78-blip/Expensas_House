// Keep infrastructure failures distinct from valid application responses.
async function readApiJson(response) {
  const type = response.headers.get('content-type') || '';
  if (!type.includes('application/json')) {
    throw new Error('La web no pudo comunicarse con la API. Revisá que el backend esté activo y conectado al despliegue.');
  }
  return response.json();
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('/api/system/info');
    const info = await readApiJson(response);
    const notice = document.getElementById('environment-notice');
    notice.hidden = info.mode !== 'demo';
  } catch { /* The sign-in form reports backend availability separately. */ }
});
