from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
from .service.folha_processos_services import buscar as buscar_pdf

load_dotenv()

app = FastAPI()

# Libera acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/buscar/{serial}")
def buscar(serial: str):
    resultado = buscar_pdf(serial)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Essa folha de processo não está no sistema! Favor, informar Engenharia Industrial."
        )

    caminho_pdf = resultado['caminho']

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

# Caminho do frontend
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve arquivos estáticos (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")