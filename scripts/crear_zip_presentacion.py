"""Package the committed, reproducible source without local credentials or data."""
from io import BytesIO
from pathlib import Path, PurePosixPath
import subprocess
import re
import argparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "Presentacion_Expensas-House/"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    revision = git("rev-parse", "HEAD").decode().strip()
    source = git("archive", "--format=zip", revision)
    with zipfile.ZipFile(BytesIO(source)) as committed:
        android_build = committed.read("app/build.gradle.kts").decode("utf-8")
    version = re.search(r'versionName\s*=\s*"([^"]+)"', android_build)[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, default=ROOT / "output" / "apk" / f"Expensas-House-{version}.apk")
    parser.add_argument("--ticket", type=Path, help="Foto autorizada para incluir solo en el ZIP, sin publicarla en Git.")
    options = parser.parse_args()
    apk = options.apk.resolve()
    ticket = options.ticket.resolve() if options.ticket else None
    if ticket is not None and (not ticket.is_file() or ticket.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}):
        raise ValueError("La foto de ejemplo no existe o su formato no es compatible.")
    if not apk.is_file():
        raise FileNotFoundError(f"Compilá Android {version} e indicá el APK con --apk. No se generó un ZIP incompleto.")
    with zipfile.ZipFile(apk) as package:
        if "AndroidManifest.xml" not in package.namelist() or "classes.dex" not in package.namelist() or package.testzip():
            raise ValueError("El APK no es válido.")
    apk_name = f"android/Expensas-House-{version}.apk"
    destination = ROOT / "output" / "Presentacion_Expensas-House.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    links = (
        "PRESENTACIÓN EXPENSAS HOUSE\n\n"
        "GitHub: https://github.com/griseldablanco78-blip/Expensas_House\n"
        "Vercel: https://expensas-house-griselda-blanco.vercel.app\n"
        "API: https://expensas-house-griselda-blanco.vercel.app/docs\n\n"
        f"Versión del código: {revision}\n\n"
        "Comenzar por README.md e INFORME_PRESENTACION.md.\n"
        "Documentación completa: https://github.com/griseldablanco78-blip/Expensas_House/tree/main/docs\n"
        "La documentación extensa queda en GitHub para simplificar la entrega.\n"
        "\n"
        "Entrega solicitada: código + este TXT con GitHub y Vercel.\n"
        "Incluye un informe breve con los seis puntos pedidos.\n"
        "La APK y la foto son material adicional solicitado por la autora.\n"
        f"APK: {apk_name}\n"
        "Copiar o descargar la APK en un teléfono Android y abrirla para instalar.\n"
        "Es una compilación de prueba; no es necesario Android Studio para ejecutarla.\n"
        "Para revisar y compilar el código Android, abrir el proyecto en Android Studio.\n"
        "Las credenciales privadas, imágenes personales y bases locales no se incluyen.\n"
        "Para ejecutar localmente, seguir las instrucciones del README.\n"
    )
    with zipfile.ZipFile(BytesIO(source)) as original, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as bundle:
        for member in original.infolist():
            name = member.filename
            path = PurePosixPath(name)
            if name.endswith("/") or name.lower().endswith(".md") or path.parts[0] == "docs":
                continue
            if name != ".env.example" and (path.name.startswith(".env") or path.suffix.lower() in {".db", ".sqlite3", ".jks", ".keystore", ".apk"}):
                raise RuntimeError(f"Archivo privado o generado inesperado en Git: {name}")
            if path.name == "local.properties" or any(part in {".git", ".runtime", "node_modules", ".venv"} for part in path.parts):
                raise RuntimeError(f"Archivo local inesperado: {name}")
            bundle.writestr(PREFIX + name, original.read(member))
        bundle.writestr(PREFIX + "INFORME_PRESENTACION.md", original.read("docs/INFORME_PRESENTACION.md"))
        short_readme = f"""# Expensas House

Entrega: código + ENLACES_PROYECTO.txt. INFORME_PRESENTACION.md reúne los seis puntos pedidos por la cátedra.
Adicionales: instalador Android {version} en android/ y, si se adjunta, foto de ejemplo en ejemplos/.

## Probar

Web: https://expensas-house-griselda-blanco.vercel.app
Android: copiar la APK a un teléfono Android y abrirla para instalar. Se conecta a la misma API pública.
Cuenta compartida de pruebas: test123 / PruebasTest1234. Sus usuarios pueden modificar el mismo hogar.

## Ejecutar el código localmente

Requiere Python 3.12 y Node.js. En la carpeta del proyecto:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
npm ci
npm run build:web
.venv/Scripts/python.exe scripts/crear_administradora.py
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload
```

Abrir http://127.0.0.1:8000 y http://127.0.0.1:8000/docs.
Android: abrir el proyecto Gradle en Android Studio; la versión incluida usa la URL fija de Vercel.

La explicación ampliada de arquitectura, tecnologías y módulos se consulta en GitHub mediante ENLACES_PROYECTO.txt.
No se incluyen bases personales ni credenciales privadas del servidor.
"""
        bundle.writestr(PREFIX + "README.md", short_readme.encode("utf-8"))
        bundle.writestr(PREFIX + "ENLACES_PROYECTO.txt", links.encode("utf-8"))
        if ticket:
            bundle.write(ticket, PREFIX + "ejemplos/Ticket_Dia" + ticket.suffix.lower())
        bundle.write(apk, PREFIX + apk_name)
    with zipfile.ZipFile(destination) as bundle:
        assert bundle.testzip() is None
        for required in (apk_name, "README.md", "INFORME_PRESENTACION.md", "ENLACES_PROYECTO.txt", "backend/app/main.py", "frontend/web/index.html", "app/build.gradle.kts", "gradlew.bat"):
            assert PREFIX + required in bundle.namelist(), required
        print(f"ZIP verificado: {destination} ({len(bundle.namelist())} archivos, {destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
