"""Repository paths, independent of the current working directory."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WEB_FRONTEND_DIR = PROJECT_ROOT / "frontend" / "web"
