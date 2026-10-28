"""Transport and browser protections; no TLS verification bypasses."""
import os
from urllib.parse import urlsplit
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class HttpSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        host = request.url.hostname or ''
        loopback = host in ('localhost', '127.0.0.1', '::1', 'testserver') and (
            request.client is None or request.client.host in ('127.0.0.1', '::1', 'testclient'))
        configured = os.getenv('EXPENSA_PUBLIC_URL', '').rstrip('/')
        allowed = {value.strip().rstrip('/') for value in os.getenv('EXPENSA_ALLOWED_ORIGINS', configured).split(',') if value.strip()}
        if loopback:
            allowed.add(str(request.base_url).rstrip('/'))
        origin = request.headers.get('origin')
        if request.url.scheme != 'https' and not loopback:
            return JSONResponse({'detail': 'Usá HTTPS para proteger el correo, la contraseña y los tickets. El acceso HTTP por Wi-Fi está deshabilitado.'}, status_code=426)
        if origin and origin.rstrip('/') not in allowed:
            return JSONResponse({'detail': 'Origen no autorizado.'}, status_code=403)
        if configured and host != urlsplit(configured).hostname and not loopback:
            return JSONResponse({'detail': 'Nombre de servidor no autorizado.'}, status_code=400)
        size = request.headers.get('content-length')
        if size:
            try:
                if int(size) > 12 * 1024 * 1024:
                    return JSONResponse({'detail': 'La solicitud es demasiado grande.'}, status_code=413)
            except ValueError:
                return JSONResponse({'detail': 'Tamaño de solicitud no válido.'}, status_code=400)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Permissions-Policy'] = 'camera=(self), microphone=(self), geolocation=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https:; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
        if request.url.path.startswith('/api/') or request.url.path in ('/stock', '/offers', '/productos_criticos', '/'):
            response.headers['Cache-Control'] = 'no-store'
        if request.url.scheme == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response
