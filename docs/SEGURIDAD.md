## Acceso actual sin correo

El modo predeterminado `EXPENSA_AUTH_MODE=password` usa un nombre de usuario y contraseña. No conecta Gmail ni envía verificaciones, invitaciones o recuperaciones por correo. El modo `email` descrito más abajo es opcional y está desactivado.

La primera administradora se crea únicamente desde la PC con `.venv/Scripts/python.exe scripts/crear_administradora.py`. El configurador pide dos veces la contraseña oculta; nunca la muestra ni la pasa por argumentos. No reemplaza cuentas existentes. El registro público permanece bloqueado hasta que existe una administradora. Ningún registro web obtiene permisos automáticamente.

Los demás usuarios crean su cuenta; luego la administradora ingresa su nombre de usuario y selecciona el perfil en Mi hogar > Actualizar permiso. Una cuenta sin permisos no puede consultar los datos del hogar.

La web permite cambiar la contraseña ingresando la actual y confirmando la nueva. El cambio revoca todas las sesiones y códigos anteriores. La recuperación por correo está desactivada: no hay un restablecimiento remoto sin prueba de identidad. El doble factor todavía no está implementado.

Compatibilidad de almacenamiento: la columna y el campo API `email` guardan el identificador de usuario; en este modo no representan un correo verificado. La columna heredada `verified` indica que la cuenta puede autenticarse, no que se haya comprobado un correo. Las cuentas pendientes del modo anterior no se activan automáticamente. Se mantiene Argon2id, HTTPS, límites de intentos, CSRF y permisos en el servidor.

---

# Seguridad, acceso por correo e invitaciones

## Estado de esta entrega

Se implementaron registro por correo y contraseña, verificación de correo, recuperación de contraseña, sesiones revocables, permisos por perfil e invitaciones desde la web. El backend protege las rutas funcionales y las rutas heredadas, incluyendo tickets, chatbot y sincronización.

El acceso HTTPS temporal permite pruebas desde dispositivos externos; la dirección vigente se configura localmente y no representa un despliegue permanente. El modo de correo requiere configuración SMTP; el modo predeterminado de usuario y contraseña no envía verificaciones por correo.

La API necesita un proceso activo en el servidor. El acceso HTTP por Wi-Fi está bloqueado; los dispositivos externos requieren una dirección HTTPS válida. Las cuentas administradoras se configuran mediante el procedimiento local documentado, sin credenciales predeterminadas.

## Protocolo de acceso implementado

1. **Registro:** correo y contraseña de entre 15 y 128 caracteres. Se guarda Argon2id, no la contraseña original.
2. **Verificación:** se envía un token aleatorio al correo. Vence a los 30 minutos, solo se usa una vez y se almacena su hash en SQLite. Al verificar, la persona elige/confirma la contraseña que quedará activa. Esto evita confiar en una contraseña registrada previamente por otra persona para ese correo.
3. **Permiso al hogar:** verificar un correo no concede acceso automáticamente. La cuenta administradora se identifica por la configuración del servidor y también debe verificar su correo. Los invitados deben tener un permiso asignado o aceptar una invitación.
4. **Inicio de sesión:** el backend compara el hash, exige verificación e impone límites de intentos por IP y correo. La respuesta de error no distingue entre contraseña incorrecta y correo sin verificar.
5. **Sesión:** un token aleatorio con ocho horas de vigencia. La base guarda su hash. Web usa cookie `HttpOnly`, `SameSite=Strict` y `Secure` bajo HTTPS; las escrituras necesitan además el token CSRF. Android usa Bearer en memoria, sin guardar contraseña ni token de sesión en preferencias.
6. **Autorización:** en cada petición se consulta el permiso vigente, incluido el acceso por rutas heredadas. Las opciones 2 y 3 no pueden modificar datos. La opción 3 recibe una sincronización sin presupuesto, gastos, ofertas ni tickets.
7. **Cierre y recuperación:** cerrar sesión revoca esa sesión. Restablecer la contraseña revoca todas las sesiones anteriores. Cambiar perfiles o revocar acceso desde Integrantes invalida las sesiones del destinatario.

Los perfiles siguen siendo: **1 lectura y escritura completas**, **2 lectura completa**, **3 lectura únicamente de stock y lista de compras**. Administrar integrantes es exclusivo de la administradora. Las consultas del chatbot y dictado son consultas permitidas para opción 2, sin conceder operaciones de escritura.

## Invitación por correo desde la web

1. La administradora entra a **Mi hogar**.
2. Ingresa el correo destinatario y elige opción **1, 2 o 3**.
3. Pulsa **Enviar invitación**. El backend envía un enlace/código de un solo uso con vigencia de 48 horas. Todavía no se activa una membresía.
4. La persona se registra, verifica ese mismo correo e inicia sesión. El enlace de invitación permite aceptarla desde la web; Android permite pegar el código recibido después de iniciar sesión.
5. La invitación solo se acepta por la cuenta autenticada con ese correo verificado. Se conserva el perfil asignado por la administradora; la persona invitada no puede elegir un permiso superior.
6. La administradora puede consultar pendientes, revocarlas y actualizar el perfil de integrantes existentes. Reenviar una invitación sustituye la anterior.

El backend no devuelve tokens de invitación ni verificación al navegador que los solicita. Los enlaces usan fragmentos `#verify`, `#reset` o `#invite` para evitar que los tokens se incluyan en las rutas de los registros HTTP. La web elimina el fragmento al procesarlo. Solo el token de invitación se conserva temporalmente en `sessionStorage` para completar el registro/inicio de sesión; no es un token de sesión general.

## Transporte y navegador

- Las peticiones HTTP de dispositivos de la Wi-Fi se rechazan con HTTP 426. No se añade ninguna excepción para enviar contraseñas al IP local por HTTP.
- Se permite HTTP exclusivamente en loopback para desarrollo desde esta PC. Android de depuración solo permite el transporte local de emulador/loopback; las direcciones Wi-Fi necesitan HTTPS.
- Se eliminaron CORS con comodín y los manejadores JavaScript inline. Los orígenes del navegador se comprueban contra la URL configurada. La interfaz se sirve junto con la API, sin necesitar CORS general.
- Se incluyen CSP, protección contra iframes, `nosniff`, política de referencias y `no-store` para datos privados. HSTS se agrega en respuestas HTTPS.
- Las fotos y solicitudes grandes tienen límites; la lectura OCR conserva su límite de tiempo. La foto se procesa en el servidor de la instalación, no en un servicio externo de OCR.
- No se deshabilita la comprobación de certificados ni se instalan certificados raíz en el teléfono automáticamente.

## Activación que falta completar

### Correo

El servidor carga `.env`. Ya existe la clave de administradora; **no reemplazar ese archivo completo**. Consultar `.env.example` y completar solo las variables faltantes:

```dotenv
EXPENSA_PUBLIC_URL=https://TU-DOMINIO-REAL
EXPENSA_ALLOWED_ORIGINS=https://TU-DOMINIO-REAL
SMTP_HOST=SERVIDOR-SMTP
SMTP_PORT=587
SMTP_MODE=starttls
SMTP_FROM=REMITENTE-AUTORIZADO
SMTP_USER=USUARIO-DEL-PROVEEDOR
SMTP_PASSWORD=CREDENCIAL-DEL-PROVEEDOR
```

Esas credenciales se ingresan en el entorno local del servidor, sin incluirlas en documentación, mensajes ni en el repositorio. El correo usado para iniciar sesión no obliga a utilizar Gmail como proveedor de envío. Si se elige SMTP de Gmail, revisar las condiciones de la cuenta y las [contraseñas de aplicación de Google](https://support.google.com/accounts/answer/185833?hl=es); no usar la contraseña habitual de Gmail en el proyecto. No se configuró ni se envió correo real en esta configuración.

### HTTPS

Se dejó `deploy/Caddyfile.example` para un dominio real. [Caddy puede gestionar certificados HTTPS](https://caddyserver.com/docs/automatic-https) cuando se cumplen los requisitos de dominio, DNS y red. No se instaló Caddy ni se modificaron DNS, puertos públicos o firewall. Todavía no hay un dominio estable propio de Expensa House; se usa únicamente la URL temporal de pruebas autorizada.

En una instalación con un proxy HTTPS en la misma máquina:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1
```

La API permanece en loopback y solo el proxy recibe conexiones externas. No utilizar `--forwarded-allow-ips=*`. El dominio del certificado debe coincidir con la URL del cliente. En Android, configurar `expensa.apiBaseUrl=https://TU-DOMINIO-REAL/` en `local.properties` y compilar de nuevo. El APK conserva la URL local anterior hasta que exista una URL real para reemplazarla; su interceptor la rechazará para credenciales por HTTP.

### Crear la cuenta administradora

Después de configurar correo y HTTPS: abrir la web, seleccionar **Crear cuenta**, usar el correo configurado como administradora y elegir una contraseña propia. Abrir el correo de verificación y confirmar el código y la contraseña. Luego iniciar sesión y usar **Mi hogar** para invitar integrantes. No hay cuenta con contraseña predeterminada ni un endpoint público que convierta al primer registro en administrador.

## Datos, respaldo y alcance

Esta entrega protege el **único hogar existente**. No promete aislamiento entre varios hogares: ese modelo requiere continuar la migración de datos descrita en la arquitectura. El inventario y los gastos existentes siguen en `data/app_state.json`; identidad, sesiones, permisos e invitaciones están en `data/accounts.sqlite3`. Ambos deben respaldarse con el servidor detenido o mediante un mecanismo coherente de respaldo. La persistencia JSON sigue requiriendo un solo proceso de Uvicorn.

Android usa una caché Room separada por ID de cuenta y preferencias de sincronización y tickets pendientes por cuenta. La antigua base local `expensa_db` no se borra ni se importa silenciosamente; cualquier dato pendiente de esa versión necesita una importación explícita para no atribuirlo a otra cuenta. Las contraseñas y tokens de sesión no se guardan en esa caché. En esta versión se debe iniciar sesión de nuevo después de cerrar/reiniciar la app.

La autorización comprueba el servidor en cada petición; no hay notificaciones push de revocación. Información que un usuario consultó legítimamente antes de una revocación no puede retirarse de una captura de pantalla o copia que ya haya realizado. El proyecto aún no incluye MFA, auditoría completa de operaciones, despliegue público verificado ni una auditoría independiente de seguridad. HTTPS y un login reducen riesgos concretos; no justifican afirmar que una aplicación es invulnerable.

## Verificación

Las pruebas usan cuentas y envío de correos simulados, nunca direcciones reales. Cubren acceso anónimo denegado, verificación y recuperación de un solo uso, hash de contraseñas, CSRF, atributos de cookie, límites de intentos, rechazo de HTTP en red local, permisos de lectura, eliminación de datos financieros del perfil 3, revocación e invitaciones ligadas al correo correcto. La plantilla de proxy y el envío real de correos quedan pendientes de verificar en la instalación final.

Referencias: [autenticación de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), [almacenamiento de contraseñas de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) y [seguridad con FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/). Se usaron sesiones opacas revocables para este proyecto; no se necesita introducir JWT para tener autenticación.


## Activación temporal de pruebas autorizada

El entorno de pruebas puede usar un Quick Tunnel de `cloudflared` habilitado explícitamente por la administración. La URL de la sesión actual está en `.runtime/public-url.txt` (archivo local ignorado por Git); también se configuró en `.env` y en `local.properties` para compilar Android. La API sigue escuchando solo en `127.0.0.1:8002`.

Se comprobó por la dirección HTTPS que la página responde 200 y que `/api/stock` responde 401 sin sesión. El túnel no sustituye el login de la aplicación. La dirección es temporal: requiere la PC y el proceso de túnel activos; al generar otro túnel habrá que actualizar URL pública, origen permitido y APK. No es un despliegue de producción.

Para introducir la credencial de correo sin pasarla por el chat:

```powershell
.\.venv\Scripts\python.exe .\scripts\configurar_correo.py
```

El configurador abre preguntas locales con Gmail como sugerencia, permite cambiar el servidor, pide la contraseña de aplicación con entrada oculta, comprueba la conexión SMTP con TLS y guarda los datos en `.env` solo si la autenticación funciona. No envía correos de prueba. En la primera configuración, el servidor detecta las variables nuevas al actualizar la web. Si se cambian credenciales que ya estaban cargadas, reiniciar el servidor.

Si se usa Gmail, consultar la [ayuda oficial para contraseñas de aplicación](https://support.google.com/accounts/answer/185833?hl=es). La contraseña habitual de Gmail y la contraseña de Expensa House no se ingresan en ese configurador.

Se agregó `/api/auth/status`, que informa únicamente si el registro está habilitado, sin mostrar remitentes ni credenciales. Si el correo todavía no está configurado, el backend devuelve 503 antes de consumir intentos de registro y la web avisa que no hace falta insistir. Esto evita repetir el bloqueo causado por probar una configuración incompleta.
