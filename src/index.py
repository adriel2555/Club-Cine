from flask import Flask, render_template, request, redirect, url_for, flash,session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2.extras
from src.database import get_db_connection
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
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash('Error de conexión con la base de datos.', 'danger')
            return render_template('login.html')

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM miembros WHERE email = %s", (email,))
        miembro = cursor.fetchone()
        cursor.close()
        conn.close()

        if miembro and check_password_hash(miembro['password_hash'], password):
            session['user_id'] = miembro['id']
            session['user_name'] = miembro['nombre']
            session['is_admin'] = miembro['es_admin']
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('dashboard'))
        else:
            # ESTA ES LA CORRECCIÓN CLAVE
            # En lugar de redirigir, volvemos a mostrar la plantilla de login con un mensaje.
            flash('Email o contraseña incorrectos. Por favor, inténtalo de nuevo.', 'danger')
            return render_template('login.html')

    # Si el método es GET, simplemente mostramos la página
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Elimina los datos del usuario de la sesión
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    flash('Has cerrado la sesión.', 'info')
    return redirect(url_for('login'))

# Ruta de Registro (opcional)
# Reemplaza tu función 'registro' por esta
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')

        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('registro.html') # Renderizar, no redirigir

        conn = get_db_connection()
        if not conn:
            flash('Error de conexión con la base de datos.', 'danger')
            return render_template('registro.html') # Renderizar, no redirigir
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM miembros WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Este correo electrónico ya está registrado. Por favor, inicia sesión.', 'warning')
            cursor.close()
            conn.close()
            return render_template('registro.html') # Renderizar, no redirigir

        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute(
                "INSERT INTO miembros (nombre, email, password_hash) VALUES (%s, %s, %s)",
                (nombre, email, password_hash)
            )
            conn.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login')) # Aquí la redirección SÍ es correcta
        except Exception as e:
            conn.rollback()
            flash(f'Ocurrió un error durante el registro: {e}', 'danger')
            return render_template('registro.html') # Renderizar, no redirigir
        finally:
            cursor.close()
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
        # Usamos 'is_admin', que es la clave que guardamos en la sesión
        if not session.get('is_admin'):
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
@login_required # Protegemos para que solo usuarios logueados vean los detalles
def detalle_sesion(id_sesion):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta 1: Detalles de la sesión. Es la más importante.
    cursor.execute("""
        SELECT s.id, s.fecha_proyeccion, s.lugar, p.titulo, m.nombre AS anfitrion
        FROM sesiones s
        JOIN peliculas p ON s.id_pelicula = p.id
        JOIN miembros m ON s.anfitrion_id = m.id
        WHERE s.id = %s;
    """, (id_sesion,))
    sesion_detalle = cursor.fetchone()

    # === COMPROBACIÓN CRUCIAL ===
    # Si la sesión no existe, no continuamos.
    if not sesion_detalle:
        flash('La sesión que buscas no existe.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))

    # Si la sesión SÍ existe, procedemos a buscar a los asistentes.
    cursor.execute("""
        SELECT m.id, m.nombre FROM asistencias a
        JOIN miembros m ON a.id_miembro = m.id
        WHERE a.id_sesion = %s;
    """, (id_sesion,))
    asistentes = cursor.fetchall()

    # Lógica para saber si el usuario actual está inscrito
    usuario_esta_inscrito = False
    id_miembro_actual = session.get('user_id')
    if id_miembro_actual:
        lista_ids_asistentes = [asistente['id'] for asistente in asistentes]
        if id_miembro_actual in lista_ids_asistentes:
            usuario_esta_inscrito = True
    
    cursor.close()
    conn.close()

    return render_template('detalle_sesion.html', 
                           sesion=sesion_detalle, 
                           asistentes=asistentes, 
                           usuario_esta_inscrito=usuario_esta_inscrito)

@app.route('/sesion/<int:id_sesion>/confirmar', methods=['POST'])
@login_required
def confirmar_asistencia(id_sesion):
    id_miembro = session['user_id']
    conn = None  # Inicializamos la conexión como None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- LÓGICA DIRECTAMENTE EN PYTHON ---

        # 1. Verificar si la sesión es en el pasado
        cursor.execute("SELECT fecha_proyeccion FROM sesiones WHERE id = %s", (id_sesion,))
        sesion = cursor.fetchone()
        if not sesion or sesion['fecha_proyeccion'] < datetime.now(sesion['fecha_proyeccion'].tzinfo):
            flash('No se puede confirmar asistencia a una sesión pasada o inexistente.', 'danger')
            return redirect(url_for('detalle_sesion', id_sesion=id_sesion))

        # 2. Verificar si el usuario ya está inscrito
        cursor.execute(
            "SELECT id FROM asistencias WHERE id_sesion = %s AND id_miembro = %s",
            (id_sesion, id_miembro)
        )
        ya_inscrito = cursor.fetchone()

        if ya_inscrito:
            flash('Ya estás inscrito en esta sesión.', 'warning')
            return redirect(url_for('detalle_sesion', id_sesion=id_sesion))

        # 3. Si todo está bien, insertar el registro
        cursor.execute(
            "INSERT INTO asistencias (id_sesion, id_miembro, confirmado) VALUES (%s, %s, %s)",
            (id_sesion, id_miembro, True)
        )
        
        # --- FIN DE LA LÓGICA ---
        
        conn.commit() # Guardamos la transacción
        flash('¡Tu asistencia ha sido confirmada con éxito!', 'success')

    except Exception as e:
        if conn:
            conn.rollback() # Si algo sale mal, revertimos los cambios
        
        # Imprimimos el error real en la terminal para saber qué pasó
        print(f"***** ERROR REAL en confirmar_asistencia: {e} *****")
        
        flash('Ocurrió un error inesperado al intentar confirmar tu asistencia.', 'danger')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('detalle_sesion', id_sesion=id_sesion))

@app.route('/sesion/<int:id_sesion>/cancelar', methods=['POST'])
@login_required # Protegemos esta ruta también
def cancelar_asistencia(id_sesion):
    # Obtenemos el ID del usuario directamente de la sesión
    id_miembro = session['user_id'] 

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM asistencias WHERE id_sesion = %s AND id_miembro = %s",
            (id_sesion, id_miembro)
        )
        conn.commit()
        flash('Has cancelado tu asistencia.', 'info')
    except Exception as e:
        conn.rollback()
        flash(f'Error al cancelar la asistencia: {e}', 'danger')
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for('detalle_sesion', id_sesion=id_sesion))

# En index.py, añade esta ruta
@app.route('/asistencias')
@login_required
def listar_asistencias():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtenemos el ID del usuario de la sesión
    id_usuario_actual = session.get('user_id')

    # Consulta simplificada
    cursor.execute("""
        SELECT 
            s.id,
            p.titulo,
            s.fecha_proyeccion,
            (SELECT COUNT(*) FROM asistencias WHERE id_sesion = s.id) AS total_asistentes
        FROM sesiones s
        JOIN peliculas p ON s.id_pelicula = p.id
        WHERE s.fecha_proyeccion > NOW()
        ORDER BY s.fecha_proyeccion ASC
    """)
    
    sesiones = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('asistencias.html', sesiones=sesiones)

if __name__ == '__main__':
    app.run(debug=True)
