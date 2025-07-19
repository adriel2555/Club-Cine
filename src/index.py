from flask import Flask, render_template, request, redirect, url_for
import os
from database import get_db_connection
from datetime import datetime

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# 🧠 Esta era la ruta duplicada: la removemos o movemos a otra
# @app.route("/")
# def test_db_connection():
#     ...

@app.route("/test-db")  # ✔️ si quieres mantener la prueba de conexión, usa otra ruta
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

@app.route('/miembros/nuevo', methods=['GET', 'POST'])
def anadir_miembro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO miembros (nombre, email) VALUES (%s, %s);", (nombre, email))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('listar_miembros'))

    return render_template('formulario_miembro.html')

@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.fecha_proyeccion, p.titulo, m.nombre AS anfitrion
        FROM sesiones s
        JOIN peliculas p ON s.id_pelicula = p.id
        JOIN miembros m ON s.anfitrion_id = m.id
        WHERE s.fecha_proyeccion > NOW()
        ORDER BY s.fecha_proyeccion ASC;
    """)
    sesiones = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('dashboard.html', sesiones=sesiones)

@app.route('/sesiones/nueva', methods=['GET', 'POST'])
def programar_sesion():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        pelicula_id = request.form['pelicula']
        fecha = request.form['fecha']
        lugar = request.form['lugar']
        anfitrion_id = request.form['anfitrion']

        try:
            cursor.execute("""
                INSERT INTO sesiones (id_pelicula, fecha_proyeccion, lugar, anfitrion_id)
                VALUES (%s, %s, %s, %s)
            """, (pelicula_id, fecha, lugar, anfitrion_id))
            conn.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            return f"❌ Error al programar sesión: {str(e)}", 500
        finally:
            cursor.close()
            conn.close()

    # GET: Obtener películas y anfitriones
    cursor.execute("SELECT id, titulo, director FROM peliculas ORDER BY titulo;")
    peliculas = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM miembros ORDER BY nombre;")
    miembros = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('programar_sesion.html', peliculas=peliculas, miembros=miembros)
    
@app.route('/sesiones/nueva', methods=['GET', 'POST'])
def nueva_sesion():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        director = request.form['director']
        fecha_str = request.form['fecha']
        lugar = request.form['lugar']
        id_anfitrion = int(request.form['id_anfitrion'])

        try:
            fecha = datetime.fromisoformat(fecha_str)  # convertir a timestamp

            # Llamar al procedimiento con los tipos correctos y en orden
            cursor.callproc('programar_nueva_sesion', (titulo, director, fecha, lugar, id_anfitrion))

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            cursor.close()
            conn.close()
            return f"❌ Error al programar sesión: {str(e)}", 500

    # Si GET: renderizar formulario con listas de películas y miembros
    cursor.execute("SELECT id, nombre FROM miembros ORDER BY nombre;")
    miembros = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('programar_sesion.html', miembros=miembros)


if __name__ == '__main__':
    app.run(debug=True)
