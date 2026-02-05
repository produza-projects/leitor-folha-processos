from dotenv import load_dotenv
import pymysql
import os
from pymysql.cursors import DictCursor

# carrega variáveis do .env
load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=DictCursor,
        connect_timeout=5,
    )
