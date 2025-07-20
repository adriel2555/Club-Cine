from flask import Flask, render_template, request, redirect, url_for, flash,session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2.extras
from database import get_db_connection
from datetime import datetime
from functools import wraps

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)
app.secret_key = '123456'

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

# Ruta de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        if conn is None:
            flash("Error: No se pudo conectar a la base de datos.", 'danger')
            return render_template('login.html')

        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            # MODIFICACIÓN: Buscar usuario en la tabla 'miembros' por email
            cur.execute("SELECT id, nombre, email, password_hash, es_admin FROM miembros WHERE email = %s", (email,))
            miembro = cur.fetchone()
            cur.close()
            conn.close()

            if miembro and check_password_hash(miembro['password_hash'], password):
                session['user_id'] = miembro['id']
                session['nombre'] = miembro['nombre']
                session['es_admin'] = miembro['es_admin'] if 'es_admin' in miembro and miembro['es_admin'] is not None else False
                flash('¡Bienvenido!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Correo o contraseña incorrectos', 'danger')
        except Exception as e:
            flash(f"Error durante el inicio de sesión: {e}", 'danger')
            if conn:
                conn.close() # Asegura que la conexión se cierre en caso de error
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('dashboard'))

# Ruta de Registro (opcional)
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['username'] # El campo de tu HTML se llama 'username'
        email = request.form.get('email')
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        if conn is None:
            flash("Error: No se pudo conectar a la base de datos.", 'danger')
            return render_template('registro.html')

        try:
            cur = conn.cursor()
            # Verificar si el email ya existe
            cur.execute("SELECT id FROM miembros WHERE email = %s", (email,))
            if cur.fetchone():
                flash('Este correo electrónico ya está registrado.', 'warning')
                return render_template('registro.html')

            # MODIFICACIÓN: Insertar en la tabla 'miembros'
            # Asegúrate que tu tabla 'miembros' tenga las columnas: id (serial), nombre, email, password_hash, es_admin (boolean default false)
            cur.execute(
                "INSERT INTO miembros (nombre, email, password_hash, es_admin) VALUES (%s, %s, %s, %s)",
                (nombre, email, password, False) # Nuevo usuario no es admin por defecto
            )
            conn.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error al registrar: {e}', 'danger')
        finally:
            if conn:
                conn.close()
    return render_template('registro.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('es_admin'):
            flash('Acceso restringido a administradores', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/miembros')
def listar_miembros():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM miembros;")
    miembros = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('miembros.html', miembros=miembros)

@app.route('/miembros/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def anadir_miembro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])  # Añadir este campo
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO miembros (nombre, email, password_hash, es_admin) VALUES (%s, %s, %s, %s);", 
            (nombre, email, password, False)
        )
        conn.commit()
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

@login_required
@admin_required
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

    now = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return render_template('programar_sesion.html', peliculas=peliculas, miembros=miembros)

@app.route('/sesion/<int:id_sesion>')
def detalle_sesion(id_sesion):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.fecha_proyeccion, s.lugar, p.titulo, m.nombre AS anfitrion
        FROM sesiones s
        JOIN peliculas p ON s.id_pelicula = p.id
        JOIN miembros m ON s.anfitrion_id = m.id
        WHERE s.id = %s
    """, (id_sesion,))
    sesion = cur.fetchone()

    cur.execute("""
        SELECT m.nombre, m.id
        FROM asistencias a
        JOIN miembros m ON a.id_miembro = m.id
        WHERE a.id_sesion = %s
    """, (id_sesion,))
    asistentes = cur.fetchall()

    id_miembro_actual = session.get('id_miembro_actual')
    inscrito = any(id_miembro_actual == a[1] for a in asistentes)

    cur.execute("SELECT id, nombre FROM miembros ORDER BY nombre;")
    miembros = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('detalle_sesion.html', sesion=sesion, asistentes=asistentes,
                           id_sesion=id_sesion, inscrito=inscrito,
                           id_miembro_actual=id_miembro_actual, miembros=miembros)

@app.route("/sesion/<int:id_sesion>/confirmar", methods=["POST"])
def confirmar_asistencia(id_sesion):
    id_miembro = request.form["id_miembro"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO asistencias (id_sesion, id_miembro) VALUES (%s, %s)", (id_sesion, id_miembro))
    conn.commit()

    conn.close()
    flash("¡Asistencia confirmada!")
    return redirect(url_for("detalle_sesion", id_sesion=id_sesion))

@app.route('/sesion/<int:id_sesion>/cancelar', methods=['POST'])
def cancelar_asistencia(id_sesion):
    id_miembro = session.get('id_miembro_actual')  # Simulamos usuario actual
    if not id_miembro:
        return "Usuario no identificado", 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asistencias WHERE id_sesion = %s AND id_miembro = %s", (id_sesion, id_miembro))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('detalle_sesion', id_sesion=id_sesion))

# En index.py, añade esta ruta
@app.route('/asistencias')
def listar_asistencias():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Consulta mejorada que incluye conteo de asistentes
    cursor.execute("""
        SELECT 
            s.id,
            p.titulo,
            s.fecha_proyeccion,
            s.lugar,
            m.nombre AS anfitrion,
            COUNT(a.id_miembro) AS total_asistentes,
            EXISTS(
                SELECT 1 FROM asistencias 
                WHERE id_sesion = s.id 
                AND id_miembro = %s
            ) AS ya_asiste
        FROM sesiones s
        JOIN peliculas p ON s.id_pelicula = p.id
        JOIN miembros m ON s.anfitrion_id = m.id
        LEFT JOIN asistencias a ON s.id = a.id_sesion
        WHERE s.fecha_proyeccion > NOW()
        GROUP BY s.id, p.titulo, s.fecha_proyeccion, s.lugar, m.nombre
        ORDER BY s.fecha_proyeccion ASC
    """, (session.get('id_miembro_actual'),))
    
    sesiones = cursor.fetchall()
    conn.close()
    return render_template('asistencias.html', sesiones=sesiones)

if __name__ == '__main__':
    app.run(debug=True)
