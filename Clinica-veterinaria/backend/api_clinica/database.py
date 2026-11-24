import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME")
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def get_connection():
    try:
        return psycopg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            row_factory=dict_row
        )
    except Exception as erro:
        print("Erro ao conectar ao PostgreSQL:", erro)
        return None


def testar_conexao():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("SELECT current_database()")
            )
            print("Conectado ao banco:", resultado.scalar())
    except Exception as erro:
        print("Erro ao conectar:", erro)


if __name__ == "__main__":
    testar_conexao()