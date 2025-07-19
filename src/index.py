from flask import Flask, render_template
from database import get_db_connection

app = Flask(__name__, template_folder='../templates', static_folder='../static')

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

@app.route('/miembros')
def listar_miembros():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, fecha_union FROM miembros ORDER BY nombre;")
    lista_miembros = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('miembros.html', miembros=lista_miembros)

if __name__ == '__main__':
    app.run(debug=True)
