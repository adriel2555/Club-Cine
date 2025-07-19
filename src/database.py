import psycopg2
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print("Error de conexión a la base de datos:", e)
        return None
