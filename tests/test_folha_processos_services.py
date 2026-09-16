from unittest.mock import patch

import pytest
from psycopg2.extras import RealDictCursor

from backend.service.folha_processos_services import buscar


class RecordingCursor:
    def __init__(self, result):
        self.result = result
        self.query = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, query, params):
        self.query = " ".join(query.split())
        self.params = params

    def fetchone(self):
        return self.result


class RecordingConnection:
    def __init__(self, result):
        self.recording_cursor = RecordingCursor(result)
        self.cursor_factory = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def cursor(self, cursor_factory=None):
        self.cursor_factory = cursor_factory
        return self.recording_cursor


def executar_busca(identificador, result):
    connection = RecordingConnection(result)
    with patch(
        "backend.service.folha_processos_services.get_connection",
        return_value=connection,
    ):
        retorno = buscar(identificador)
    return retorno, connection


@pytest.mark.parametrize("codigo_produto", ["5000.001622", "5001.009867"])
def test_busca_codigo_produto_por_igualdade_exata(codigo_produto):
    result = {
        "id_caminhno": 10,
        "cod_produto": codigo_produto,
        "ordem_fabricacao": None,
        "caminho": "/mnt/boro_documentacao_geral/folha.pdf",
    }

    retorno, connection = executar_busca(codigo_produto, result)

    query = connection.recording_cursor.query
    assert "FROM caminhos c" in query
    assert "WHERE c.cod_produto = %s" in query
    assert "JOIN ordens_fabricacao" not in query
    assert " LIKE " not in query.upper()
    assert connection.recording_cursor.params == (codigo_produto,)
    assert connection.cursor_factory is RealDictCursor
    assert retorno == result


@pytest.mark.parametrize(
    ("identificador", "ordem_esperada"),
    [
        ("2619006", "2619006"),
        ("261900612345", "2619006"),
        ("5000001622", "5000001"),
        ("5000.0016229", "5000.00"),
    ],
)
def test_valor_que_nao_e_codigo_produto_segue_fluxo_de_of(
    identificador, ordem_esperada
):
    result = {
        "id_caminhno": 20,
        "cod_produto": "5000.001622",
        "ordem_fabricacao": int(ordem_esperada) if ordem_esperada.isdigit() else None,
        "caminho": "/mnt/boro_documentacao_geral/folha.pdf",
    }

    retorno, connection = executar_busca(identificador, result)

    query = connection.recording_cursor.query
    assert "LEFT JOIN ordens_fabricacao o" in query
    assert "WHERE o.ordem_fabricacao = %s" in query
    assert connection.recording_cursor.params == (ordem_esperada,)
    assert retorno == result


def test_codigo_produto_inexistente_retorna_none():
    retorno, connection = executar_busca("5000.999999", None)

    assert connection.recording_cursor.params == ("5000.999999",)
    assert retorno is None
