import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            os.getenv("DATABASE_URL"),
            cursor_factory=RealDictCursor
        )
        print("Conexión a la base de datos exitosa.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"No se pudo conectar a la base de datos: {e}")
        return None
