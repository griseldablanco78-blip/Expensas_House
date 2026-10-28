"""Check the Android-configured server without credentials or private household data."""
import argparse
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', help='HTTPS URL of the API; defaults to local.properties')
    options = parser.parse_args()
    url = options.url
    if not url:
        properties = Path(__file__).resolve().parents[1] / 'local.properties'
        url = next((line.split('=', 1)[1].strip() for line in properties.read_text(encoding='utf-8').splitlines()
                    if line.startswith('expensa.apiBaseUrl=')), '')
    if not url:
        print('ERROR: falta configurar la URL de API para Android.')
        return 1
    base = url.rstrip('/')
    if not base.startswith('https://'):
        print('ERROR: el teléfono requiere una dirección HTTPS pública; localhost solo sirve en la PC.')
        return 1
    print('Servidor configurado:', base)
    for path, expected in [('/api/auth/status', 200), ('/api/expenses', 401)]:
        try:
            with urlopen(base + path, timeout=15) as response:
                status = response.status
        except HTTPError as error:
            status = error.code
        except (URLError, TimeoutError, OSError) as error:
            print('ERROR de conexión:', type(error).__name__, str(error))
            print('Revisar Internet, backend y vigencia del dominio/túnel antes de probar OCR.')
            return 1
        print(path, 'HTTP', status, 'OK' if status == expected else 'INESPERADO')
        if status != expected:
            return 1
    print('Conexión disponible; datos privados protegidos. La carga autenticada requiere probar el ticket con tu sesión.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
