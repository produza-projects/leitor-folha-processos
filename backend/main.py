from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from .database_cache import DatabaseCache
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

# Instância global do cache
db_cache = DatabaseCache()

if not DATA_BASE_PATH:
    raise RuntimeError("Variável de ambiente CAMINHO_DATABASE_FP não foi definida")

def buscar_pdf(serial: str) -> str | None:
    if not DATA_BASE_PATH or not os.path.exists(DATA_BASE_PATH):
        return None

    # Carrega o database no cache se necessário
    db_cache.load_database(DATA_BASE_PATH)
    
    # Busca no cache
    return db_cache.buscar(serial)


@app.get("/buscar/{serial}")
def buscar(serial: str):
    caminho_pdf = buscar_pdf(serial)

    if not caminho_pdf:
        raise HTTPException(
            status_code=404,
            detail="Essa folha de processo não está no sistema! Favor, informar Engenharia Industrial."
        )

    if not os.path.exists(caminho_pdf):
        raise HTTPException(
            status_code=404,
            detail="Arquivo PDF não encontrado no caminho informado."
        )
    
    #Cria a resposta e adiciona headers para desabilitar cache
    response = FileResponse(
        path=caminho_pdf,
        media_type="application/pdf",
        filename=os.path.basename(caminho_pdf)
    )
    
    # Adiciona headers para desabilitar cache do navegador
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

# Endpoint de debug
# @app.get("/status")
# def status():
#     return {
#         "registros": len(db_cache.cache),
#         "ultima_atualizacao": db_cache.last_modified
#     }

# Caminho do frontend
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve arquivos estáticos (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")