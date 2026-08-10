from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
from typing import Any

from .auth import OIDCClient, OIDCSettings, require_user
from .service.folha_processos_services import buscar as buscar_pdf

load_dotenv()

FRONTEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
router = APIRouter()


def create_app(
    settings: OIDCSettings | None = None,
    oidc_client: OIDCClient | None = None,
) -> FastAPI:
    settings = settings or OIDCSettings.from_env()
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    application.state.oidc_settings = settings
    application.state.oidc_client = oidc_client or OIDCClient(settings)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="fp_session",
        max_age=settings.session_max_age,
        same_site="lax",
        https_only=settings.cookie_secure,
    )
    application.mount(
        "/static", StaticFiles(directory=FRONTEND_PATH), name="frontend-static"
    )
    application.include_router(router)
    return application


@router.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok"}


@router.get("/", include_in_schema=False)
async def index(request: Request):
    if request.app.state.oidc_settings.enabled and not request.session.get("user"):
        return RedirectResponse("/login", status_code=302)
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))


@router.get("/login", include_in_schema=False)
async def login(request: Request, return_to: str = Query(default="/")):
    if not request.app.state.oidc_settings.enabled:
        return RedirectResponse("/", status_code=302)
    return request.app.state.oidc_client.start_login(request, return_to)


@router.get("/auth/callback", include_in_schema=False)
async def auth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        raise HTTPException(401, "Login cancelado ou recusado pelo provedor.")
    if not code or not state:
        raise HTTPException(400, "Resposta OIDC incompleta.")
    return_to = await request.app.state.oidc_client.finish_login(request, code, state)
    return RedirectResponse(return_to, status_code=302)


@router.get("/logout", include_in_schema=False)
async def logout(request: Request):
    if not request.app.state.oidc_settings.enabled:
        request.session.clear()
        return RedirectResponse("/", status_code=302)
    return request.app.state.oidc_client.logout_response(request)


@router.get("/api/me", include_in_schema=False)
async def current_user(user: dict[str, Any] = Depends(require_user)):
    return user


def _iter_pdf_file(path: str, chunk_size: int = 1024 * 1024):
    with open(path, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk


@router.get("/buscar/{serial}", include_in_schema=False)
def buscar(serial: str, _user: dict[str, Any] = Depends(require_user)):
    resultado = buscar_pdf(serial)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Essa folha de processo não está no sistema! Favor, informar Engenharia Industrial."
        )

    caminho_pdf = resultado["caminho"]

    if not os.path.exists(caminho_pdf):
        raise HTTPException(
            status_code=404,
            detail="Arquivo PDF não encontrado no caminho informado."
        )

    try:
        response = StreamingResponse(
            _iter_pdf_file(caminho_pdf),
            media_type="application/pdf",
        )
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao ler o arquivo PDF."
        )

    filename = os.path.basename(caminho_pdf)

    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


app = create_app()
