from backend.db.connection import get_connection
from dotenv import load_dotenv
import os

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_TABELA_FOLHAS = os.getenv("DB_TABELA_FOLHAS")

def buscar(of):
    query = f"""
        SELECT caminho
        FROM {DB_NAME}.{DB_TABELA_FOLHAS}
        WHERE of = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, of)
            return cursor.fetchone()
