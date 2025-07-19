from flask import Flask
from database import get_db_connection

app = Flask(__name__)

@app.route("/")
def test_db_connection():
    conn = get_db_connection()
    if conn is None:
        return "❌ Conexión fallida a la base de datos", 500
    try:
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return f"✅ Conexión exitosa. Fecha actual: {result[0]}"
    except Exception as e:
        return f"❌ Error ejecutando consulta: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
