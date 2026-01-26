from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Libera acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_BASE_PATH = os.getenv("CAMINHO_DATABASE_FP")

if not DATA_BASE_PATH:
    raise RuntimeError(
        "Variável de ambiente CAMINHO_DATABASE_FP não foi definida"
    )


def buscar_pdf(serial: str) -> str | None:
    if not DATA_BASE_PATH or not os.path.exists(DATA_BASE_PATH):
        return None

    with open(DATA_BASE_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            if ";" not in linha:
                continue

            codigo, caminho = linha.strip().split(";", 1)
            if codigo.strip() == serial:
                return caminho.strip()

    return None


@app.get("/buscar/{serial}")
def buscar(serial: str):
    caminho_pdf = buscar_pdf(serial)

    if not caminho_pdf:
        raise HTTPException(
            status_code=404,
            detail="Esse folha de processo não está no sistema! Favor, informar Engenharia Industrial."
        )

    if not os.path.exists(caminho_pdf):
        raise HTTPException(
            status_code=404,
            detail="Arquivo PDF não encontrado no caminho informado."
        )

    return FileResponse(
        path=caminho_pdf,
        media_type="application/pdf",
        filename=os.path.basename(caminho_pdf)
    )

# Caminho do frontend
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve arquivos estáticos (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")