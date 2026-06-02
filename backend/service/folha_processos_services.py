from backend.db.connection import get_connection
from psycopg2.extras import RealDictCursor


def buscar(of):
    query = """
        SELECT c.id as id_caminhno, c.cod_produto, o.ordem_fabricacao, c.caminho
        FROM caminhos c
        LEFT JOIN ordens_fabricacao o
        ON o.caminho_id = c.id
        WHERE o.ordem_fabricacao = %s
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (of,))
            return cursor.fetchone()
