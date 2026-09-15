import re

from backend.db.connection import get_connection
from psycopg2.extras import RealDictCursor


CODIGO_PRODUTO_PATTERN = re.compile(r"\d{4}\.\d{6}", flags=re.ASCII)

BUSCA_POR_PRODUTO_QUERY = """
        SELECT c.id as id_caminhno,
               c.cod_produto,
               NULL as ordem_fabricacao,
               c.caminho
        FROM caminhos c
        WHERE c.cod_produto = %s
    """

BUSCA_POR_OF_QUERY = """
        SELECT c.id as id_caminhno, c.cod_produto, o.ordem_fabricacao, c.caminho
        FROM caminhos c
        LEFT JOIN ordens_fabricacao o
        ON o.caminho_id = c.id
        WHERE o.ordem_fabricacao = %s
    """


def buscar(identificador: str):
    if CODIGO_PRODUTO_PATTERN.fullmatch(identificador):
        query = BUSCA_POR_PRODUTO_QUERY
        valor_busca = identificador
    else:
        query = BUSCA_POR_OF_QUERY
        valor_busca = identificador[:7]

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (valor_busca,))
            return cursor.fetchone()
