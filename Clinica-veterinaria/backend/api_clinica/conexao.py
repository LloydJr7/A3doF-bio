import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = "localhost"
DB_NAME = "clinica_db"
DB_USER = "postgres"
DB_PASS = "erico0312"
DB_PORT = "5432"

def get_connection():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            cursor_factory=RealDictCursor
        )
        return connection
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None
