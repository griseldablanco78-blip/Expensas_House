"""Composition root for the shared Android and web API."""
from dotenv import load_dotenv
from backend.app.core.paths import PROJECT_ROOT
load_dotenv(PROJECT_ROOT / ".env")

from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.app.core.paths import WEB_FRONTEND_DIR
from backend.app.api.routes import stock, shopping, budget, offers, chat, voice, sync, receipts, legacy
from backend.app.api.routes import auth
from backend.app.core.security import require_member
from backend.app.core.http_security import HttpSecurityMiddleware


def create_app():
    application = FastAPI(title="Expensa House API & Web", version="2.0.0",
        description="API compartida de inventario, compras, presupuesto y tickets.")
    application.add_middleware(HttpSecurityMiddleware)
    application.include_router(auth.router)
    application.include_router(auth.members_router)
    for module in (stock, shopping, budget, offers, chat, voice, sync, receipts, legacy):
        application.include_router(module.router, dependencies=[Depends(require_member)])
    application.mount("/static", StaticFiles(directory=WEB_FRONTEND_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB_FRONTEND_DIR / "index.html")

    return application


app = create_app()
