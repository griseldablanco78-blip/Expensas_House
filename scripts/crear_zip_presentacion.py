"""Package the committed, reproducible source without local credentials or data."""
from io import BytesIO
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "Presentacion_Expensas-House/"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    revision = git("rev-parse", "HEAD").decode().strip()
    source = git("archive", "--format=zip", revision)
    destination = ROOT / "output" / "Presentacion_Expensas-House.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    links = (
        "PRESENTACIÓN EXPENSAS HOUSE\n\n"
        "GitHub: https://github.com/griseldablanco78-blip/Expensas_House\n"
        "Vercel: https://expensas-house-griselda-blanco.vercel.app\n"
        "API: https://expensas-house-griselda-blanco.vercel.app/docs\n\n"
        f"Versión del código: {revision}\n\n"
        "Comenzar por README.md y docs/Presentacion_Expensas-House.md.\n"
        "Arquitectura y módulos: docs/GUIA_CODIGO.md.\n"
        "Modelos y métricas: CUADERNILLO_TECNICO_IA.md.\n"
        "Tickets y ofertas: docs/ACTUALIZACION_TICKETS_OFERTAS.md.\n\n"
        "El ZIP contiene el código versionado, instrucciones y pruebas.\n"
        "Las credenciales privadas, imágenes personales y bases locales no se incluyen.\n"
        "Para ejecutar localmente, seguir las instrucciones del README.\n"
    )
    with zipfile.ZipFile(BytesIO(source)) as original, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as bundle:
        for member in original.infolist():
            name = member.filename
            path = PurePosixPath(name)
            if name.endswith("/"):
                continue
            if name != ".env.example" and (path.name.startswith(".env") or path.suffix.lower() in {".db", ".sqlite3", ".jks", ".keystore", ".apk"}):
                raise RuntimeError(f"Archivo privado o generado inesperado en Git: {name}")
            if path.name == "local.properties" or any(part in {".git", ".runtime", "node_modules", ".venv"} for part in path.parts):
                raise RuntimeError(f"Archivo local inesperado: {name}")
            bundle.writestr(PREFIX + name, original.read(member))
        bundle.writestr(PREFIX + "ENLACES_PROYECTO.txt", links.encode("utf-8"))
    with zipfile.ZipFile(destination) as bundle:
        assert bundle.testzip() is None
        for required in ("README.md", "ENLACES_PROYECTO.txt", "backend/app/main.py", "frontend/web/index.html", "app/build.gradle.kts", "gradlew.bat"):
            assert PREFIX + required in bundle.namelist(), required
        print(f"ZIP verificado: {destination} ({len(bundle.namelist())} archivos, {destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
