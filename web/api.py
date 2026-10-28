"""Legacy Uvicorn entry point. Prefer backend.app.main:app for new setups."""
from backend.app.main import app, create_app
