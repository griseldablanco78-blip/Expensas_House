// The session cookie is HttpOnly. Passwords and session tokens never enter localStorage.
const originalFetch = window.fetch.bind(window);
window.currentUser = null;
window.canEditHousehold = () => ['admin', 'full_editor'].includes(window.currentUser?.role);
window.fetch = async (input, options = {}) => {
  const url = new URL(typeof input === 'string' ? input : input.url, location.href);
  const headers = new Headers(options.headers || (input instanceof Request ? input.headers : undefined));
  if (url.origin === location.origin) {
    const csrf = document.cookie.split('; ').find(row => row.startsWith('expensa_csrf='))?.split('=').slice(1).join('=');
    if (csrf) headers.set('X-CSRF-Token', decodeURIComponent(csrf));
  }
  const response = await originalFetch(input, {...options, headers, credentials: 'same-origin'});
  if (response.status === 401 && window.currentUser && !url.pathname.startsWith('/api/auth/')) location.reload();
  return response;
};

async function bootAuthentication(onReady) {
  const panel = document.getElementById('auth-panel');
  const shell = document.getElementById('app-shell');
  const status = document.getElementById('auth-status');
  const form = document.getElementById('auth-form');
  const mode = document.getElementById('auth-mode');
  const email = document.getElementById('auth-email');
  const password = document.getElementById('auth-password');
  const code = document.getElementById('auth-code');
  let started = false;
  let registrationAvailable = false;
  let setupMessage = 'Primero creá tu cuenta administradora en el configurador local.';
  async function showUser(user) {
    window.currentUser = user;
    const invitation = sessionStorage.getItem('expensa_invitation');
    if (invitation) {
      try {
        const response = await fetch('/api/auth/accept-invitation', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:invitation})});
        const data = await response.json();
        if (response.ok) { user = data.user; window.currentUser = user; sessionStorage.removeItem('expensa_invitation'); }
        else status.textContent = data.detail;
      } catch { status.textContent = 'No se pudo aceptar la invitación. Intentá de nuevo.'; }
    }
    if (!user.role) { status.textContent = 'Cuenta creada. La administradora todavía debe asignarte un permiso para este hogar.'; return; }
    panel.hidden = true; shell.hidden = false;
    document.body.classList.toggle('read-only', !canEditHousehold());
    document.body.classList.toggle('inventory-only', user.role === 'inventory_viewer');
    document.getElementById('session-email').textContent = user.email;
    document.getElementById('members-nav').hidden = user.role !== 'admin';
    if (!started) { started = true; onReady(); }
  }
  if (location.hash) history.replaceState(null, '', location.pathname);
  function fields() {
    const changing = mode.value === 'change-password';
    email.required = true; password.required = true; code.required = false;
    email.parentElement.hidden = false; password.parentElement.hidden = false; code.parentElement.hidden = true;
    for (const id of ['auth-new-password', 'auth-confirm-password']) {
      const input = document.getElementById(id); input.required = changing; input.parentElement.hidden = !changing; input.value = '';
    }
    password.value = ''; password.minLength = mode.value === 'register' ? 15 : 1;
    password.autocomplete = mode.value === 'register' ? 'new-password' : 'current-password';
    document.getElementById('auth-heading').textContent = changing ? 'Renová tu contraseña.' : mode.value === 'register' ? 'Tu hogar empieza acá.' : 'Qué bueno verte.';
    document.getElementById('auth-password-label').textContent = changing ? 'Contraseña actual' : 'Contraseña';
    document.getElementById('auth-submit').textContent = changing ? 'Guardar nueva contraseña' : mode.value === 'register' ? 'Crear mi cuenta' : 'Ingresar a mi hogar →';
    document.getElementById('auth-password-hint').hidden = mode.value === 'login';
    status.textContent = '';
  }
  fields(); mode.addEventListener('change', fields);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (mode.value === 'register' && !registrationAvailable) {
      status.textContent = setupMessage;
      return;
    }
    const button = form.querySelector('[type=submit]'); button.disabled = true;
    try {
      const changing = mode.value === 'change-password';
      if (changing && document.getElementById('auth-new-password').value !== document.getElementById('auth-confirm-password').value) throw new Error('Las contraseñas nuevas no coinciden.');
      const payload = changing ? {email:email.value,current_password:password.value,new_password:document.getElementById('auth-new-password').value} : mode.value === 'login' ? {email:email.value, password:password.value, client:'web'}
        : mode.value === 'register' ? {email:email.value, password:password.value}
        : ['verify', 'reset-password'].includes(mode.value) ? {token:code.value.trim(), password:password.value}
        : {email:email.value};
      const response = await fetch(`/api/auth/${changing ? 'change-password-at-login' : mode.value}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Revisá los datos del formulario.');
      password.value = '';
      document.getElementById('auth-new-password').value = ''; document.getElementById('auth-confirm-password').value = '';
      if (changing) { mode.value = 'login'; fields(); }
      if (data.user) await showUser(data.user);
      else { status.textContent = data.message; if (['verify', 'reset-password'].includes(mode.value)) {code.value = ''; mode.value = 'login'; fields();} }
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; }
  });
  document.getElementById('session-logout').addEventListener('click', async () => {
    const response = await fetch('/api/auth/logout', {method:'POST'});
    if (response.ok || response.status === 401) location.reload();
  });
  try {
    const setupResponse = await fetch('/api/auth/status');
    if (setupResponse.ok) {
      const setup = await setupResponse.json();
      registrationAvailable = setup.registration_available;
      setupMessage = setup.message;
      if (!registrationAvailable) status.textContent = setup.message;
    }
    const response = await fetch('/api/auth/me');
    if (response.ok) showUser((await response.json()).user);
  } catch { status.textContent = 'No se pudo contactar al servidor. Intentá más tarde.'; }
}

async function setupMembers() {
  const form = document.getElementById('member-form');
  const status = document.getElementById('member-status');
  async function refresh() {
    if (window.currentUser?.role !== 'admin') return;
    const response = await fetch('/api/members');
    if (!response.ok) return;
    const container = document.getElementById('members-list'); container.replaceChildren();
    const pendingResponse = await fetch('/api/members/invitations');
    const pending = pendingResponse.ok ? await pendingResponse.json() : [];
    const active = await response.json();
    for (const member of [...active, ...pending.map(item => ({...item, pending:true}))]) {
      const row = document.createElement('p'); row.textContent = `${member.email} · ${member.role}${member.pending ? ' · Invitación pendiente' : ''} `;
      if (member.role !== 'admin') {
        const remove = document.createElement('button'); remove.textContent = 'Revocar acceso';
        remove.addEventListener('click', async () => {
          const res = await fetch('/api/members', {method:'DELETE', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:member.email})});
          const data = await res.json(); status.textContent = data.message || data.detail; await refresh();
        }); row.appendChild(remove);
      }
      container.appendChild(row);
    }
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const endpoint = event.submitter?.value === 'update' ? '/api/members' : '/api/members/invitations';
    const response = await fetch(endpoint, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:document.getElementById('member-email').value, profile:document.getElementById('member-profile').value})});
    const data = await response.json(); status.textContent = data.message || data.detail; await refresh();
  });
  await refresh();
}
