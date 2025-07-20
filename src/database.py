import os
import psycopg2
from psycopg2.extras import RealDictCursor # <-- IMPORTANTE: Importa esto
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            # Le decimos a la conexión que todos los cursores que cree
            # deben ser de tipo RealDictCursor.
            cursor_factory=RealDictCursor # <-- IMPORTANTE: Añade esta línea
        )
        print("Conexión a la base de datos exitosa.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"No se pudo conectar a la base de datos: {e}")
        return None