from unittest.mock import patch

import httpx
import pytest

from backend.auth import OIDCSettings
from backend.main import create_app


def local_settings() -> OIDCSettings:
    return OIDCSettings(
        enabled=False,
        public_issuer="",
        internal_issuer="",
        client_id="",
        client_secret="",
        session_secret="local-test-session-secret-with-32-characters",
        redirect_uri="",
        post_logout_redirect_uri="",
        required_role="viewer",
        session_max_age=3600,
        cookie_secure=False,
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"


def application_client():
    application = create_app(local_settings())
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url="http://test",
    )


@pytest.mark.anyio
@pytest.mark.parametrize("codigo_produto", ["5000.001622", "5001.009867"])
async def test_codigo_produto_usa_fluxo_existente_para_retornar_pdf(
    tmp_path, codigo_produto
):
    pdf_path = tmp_path / "folha.pdf"
    pdf_content = b"%PDF-1.4\nconteudo de teste\n"
    pdf_path.write_bytes(pdf_content)

    with patch(
        "backend.main.buscar_pdf", return_value={"caminho": str(pdf_path)}
    ) as buscar_pdf:
        async with application_client() as client:
            response = await client.get(f"/buscar/{codigo_produto}")

    buscar_pdf.assert_called_once_with(codigo_produto)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'inline; filename="folha.pdf"'
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert response.content == pdf_content


@pytest.mark.anyio
async def test_codigo_produto_inexistente_mantem_resposta_404():
    with patch("backend.main.buscar_pdf", return_value=None) as buscar_pdf:
        async with application_client() as client:
            response = await client.get("/buscar/5000.999999")

    buscar_pdf.assert_called_once_with("5000.999999")
    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Essa folha de processo não está no sistema! "
            "Favor, informar Engenharia Industrial."
        )
    }


@pytest.mark.anyio
async def test_registro_com_arquivo_ausente_mantem_resposta_404(tmp_path):
    missing_pdf = tmp_path / "inexistente.pdf"

    with patch(
        "backend.main.buscar_pdf", return_value={"caminho": str(missing_pdf)}
    ):
        async with application_client() as client:
            response = await client.get("/buscar/5000.001622")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Arquivo PDF não encontrado no caminho informado."
    }
