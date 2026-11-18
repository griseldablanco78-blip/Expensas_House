"""Create the classroom ZIP: versioned source plus one TXT with GitHub and Vercel."""
from io import BytesIO
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "Expensas-House/"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    revision = git("rev-parse", "HEAD").decode().strip()
    source = git("archive", "--format=zip", revision)
    destination = ROOT / "output" / "Presentacion_Expensas-House.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    links = (
        "GitHub: https://github.com/griseldablanco78-blip/Expensas_House\n"
        "Vercel: https://expensas-house-griselda-blanco.vercel.app\n"
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
        bundle.writestr(PREFIX + "ENLACES_PROYECTO.txt", links.encode("utf-8"))
    with zipfile.ZipFile(destination) as bundle:
        assert bundle.testzip() is None
        for required in ("ENLACES_PROYECTO.txt", "backend/app/main.py", "frontend/web/index.html", "app/build.gradle.kts", "gradlew.bat"):
            assert PREFIX + required in bundle.namelist(), required
        assert not any(name.lower().endswith((".apk", ".md")) for name in bundle.namelist())
        print(f"ZIP verificado: {destination} ({len(bundle.namelist())} archivos, {destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
