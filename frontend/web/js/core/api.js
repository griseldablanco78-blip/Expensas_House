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
    if (info.mode === 'demo') document.getElementById('environment-notice').hidden = false;
  } catch { /* The sign-in form reports backend availability separately. */ }
});
