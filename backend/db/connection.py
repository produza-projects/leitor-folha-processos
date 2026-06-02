import os
import psycopg2

from dotenv import load_dotenv

load_dotenv()


def get_connection():
    server_host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT')
    database = os.getenv('POSTGRES_DATABASE')
    user = os.getenv('POSTGRES_USERNAME')
    password = os.getenv('POSTGRES_PASSWORD')

    conn = psycopg2.connect(
        host=server_host,
        port=port,
        database=database,
        user=user,
        password=password
    )

    return conn
