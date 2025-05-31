from flask import Blueprint, request, jsonify, render_template,session,url_for, flash, current_app, redirect
import sys
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
import threading
import time
from modelo import base_datos
import psutil
import redis
import scrypt
import base64
# ... tus otros imports como Blueprint, request, jsonify, etc.
# Dentro de controlador/login.py
# ... otros imports ...
from . import captura_paquetes # El '.' indica import relativo del mismo paquete/directorio
from datetime import datetime # Necesaria para la función de obtener paquetes
# Dentro de controlador/login.py
# ... otros imports ...
from . import captura_paquetes # El '.' indica import relativo del mismo paquete/directorio
from datetime import datetime # Necesaria para la función de obtener paquetes

from modelo.base_datos import (
    obtener_conexion,
    contar_usuarios,
    contar_dispositivos,
    obtener_eventos,
    obtener_ultimos_eventos,
    obtener_alertas,
    obtener_alertas_nuevas,
    obtener_usuario_por_email,
    actualizar_contraseña_usuario
)
from modelo.eventos import registrar_evento



# Define el Blueprint. El nombre del Blueprint es 'login'.
login_bp = Blueprint('login', __name__, template_folder="../vista")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@login_bp.route('/')
def home():
    """Ruta principal que renderiza la página de login."""
    return render_template("login.html")


@login_bp.route('/dashboard')
def dashboard():
    """Ruta del dashboard, requiere que el usuario esté logueado."""
    if 'usuario' not in session:
        # CORRECCIÓN: Usar 'login.home' para referenciar la ruta home del Blueprint 'login'
        return redirect(url_for('login.home'))

    total_usuarios = contar_usuarios()
    total_dispositivos = contar_dispositivos()
    resumen_monitoreo = obtener_eventos()

    ultimos_eventos = obtener_ultimos_eventos()
    alertas = obtener_alertas()

    return render_template('dashboard.html',
                           usuario=session['usuario'],
                           total_usuarios=total_usuarios,
                           total_dispositivos=total_dispositivos,
                           resumen_monitoreo=resumen_monitoreo,
                           ultimos_eventos=ultimos_eventos,
                           alertas=alertas)


@login_bp.route('/dashboard_admin')
def dashboard_admin():
    """Ruta del dashboard para administradores."""
    return render_template('dashboard_admin.html')

@login_bp.route('/logout')
def logout():
    """Ruta para cerrar la sesión del usuario."""
    usuario = session.get('usuario')
    if usuario:
        registrar_evento(usuario, "Logout", "Cierre de sesión")
    session.clear()
    # CORRECCIÓN: Usar 'login.home' para referenciar la ruta home del Blueprint 'login'
    return redirect(url_for('login.home'))

@login_bp.route('/monitoreo')
def monitoreo():
    """Ruta para la página de monitoreo de red."""
    return render_template("monitoreoRed.html")

@login_bp.route('/usuario')
def usuario():
    """Ruta para la página de gestión de usuario (individual)."""
    return render_template("usuario.html")

@login_bp.route('/perfil')
def perfil():
    """Ruta para la página de perfil de usuario."""
    return render_template("perfil.html")

@login_bp.route('/reportes')
def reportes():
    """Ruta para la página de reportes."""
    return render_template("reportes.html")


# CONFIGURACION DEL LOGIN
# Configura conexión a Redis (ajusta host/puerto si necesario)
r = redis.Redis(host='localhost', port=6379, db=0)

MAX_INTENTOS = 5
TIEMPO_BLOQUEO = 300 # en segundos, ej 5 minutos

def obtener_ip_cliente():
    """Obtiene la dirección IP del cliente que realiza la solicitud."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr




@login_bp.route('/login', methods=['POST'])
def login():
    """Maneja las solicitudes de inicio de sesión."""
    ip = obtener_ip_cliente()
    key_intentos = f"login_intentos:{ip}"
    key_bloqueo = f"login_bloqueado:{ip}"

    if r.exists(key_bloqueo):
        tiempo_restante = r.ttl(key_bloqueo)
        return jsonify({
            "status": "error",
            "mensaje": f"Demasiados intentos fallidos. Intenta nuevamente en {tiempo_restante} segundos."
        }), 429

    datos = request.json
    email = datos.get('email')
    contrasena_texto_plano = datos.get('contrasena')

    if not email or not contrasena_texto_plano:
        return jsonify({"status": "error", "mensaje": "⚠️ Por favor, completa todos los campos."}), 400

    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"status": "error", "mensaje": "🚨 Error en el sistema. No se pudo conectar a la base de datos."}), 500

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, nombre, email, contrasena, id_perfil FROM usuario WHERE email = %s AND estado = 'activo'", (email,)) # Asegúrate que el usuario esté activo
        usuario_db = cursor.fetchone()

        # ----- MODIFICACIÓN IMPORTANTE AQUÍ -----
        # Ya no usamos check_password_hash, usamos nuestra función personalizada
        if usuario_db and verificar_contrasena_scrypt(contrasena_texto_plano, usuario_db['contrasena']):
        # -----------------------------------------
            r.delete(key_intentos)
            session['usuario'] = usuario_db['nombre']
            session['id_usuario'] = usuario_db['id_usuario']
            session['perfil'] = usuario_db['id_perfil']
            # Actualizar ultimo_acceso
            try:
                cursor_update = conexion.cursor() # Usar un nuevo cursor si el anterior podría tener resultados pendientes
                cursor_update.execute("UPDATE usuario SET ultimo_acceso = NOW() WHERE id_usuario = %s", (usuario_db['id_usuario'],))
                conexion.commit()
                cursor_update.close()
            except Exception as e_update:
                print(f"Error al actualizar ultimo_acceso: {e_update}")
                # No fallar el login por esto, pero registrarlo

            registrar_evento(usuario_db['nombre'], "Inicio de sesión exitoso", f"Usuario {email} inició sesión.")


            return jsonify({
                "status": "success",
                "mensaje": f"✅ Bienvenido {usuario_db['nombre']} 🎉",
                "usuario": usuario_db['nombre'],
                "perfil": usuario_db['id_perfil']
            }), 200
        else:
            # (Tu lógica de intentos fallidos y bloqueo de IP sigue igual)
            intentos = r.incr(key_intentos)
            if intentos == 1:
                r.expire(key_intentos, TIEMPO_BLOQUEO)

            if intentos > MAX_INTENTOS:
                r.set(key_bloqueo, 1, ex=TIEMPO_BLOQUEO)
                registrar_evento(email, "Bloqueo de IP por múltiples intentos fallidos", f"IP: {ip}")
                return jsonify({
                    "status": "error",
                    "mensaje": f"❌ Demasiados intentos fallidos. IP bloqueada por {TIEMPO_BLOQUEO} segundos."
                }), 429
            else:
                # Registrar intento fallido si el usuario existe pero la contraseña no
                if usuario_db: # El email existía pero la contraseña fue incorrecta
                     registrar_evento(email, "Intento de inicio de sesión fallido", f"Contraseña incorrecta para {email}.")
                # Si usuario_db es None, el email no fue encontrado.
                # El mensaje genérico de "Credenciales incorrectas" es bueno para no revelar si el email existe.
                return jsonify({
                    "status": "error",
                    "mensaje": "❌ Credenciales incorrectas.",
                    "intentos_restantes": MAX_INTENTOS - intentos if usuario_db else MAX_INTENTOS # Ajustar si el email no existe
                }), 401
    except Exception as e:
        print("Error al iniciar sesión:", e)
        registrar_evento(email, "Error en inicio de sesión", f"Detalle: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "⚠️ Ocurrió un problema inesperado.",
            "detalle": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()





# Esta constante debe coincidir con la usada al crear los hashes (64 bytes)
# que resultan en 128 caracteres hexadecimales.
SCRYPT_VERIFY_BUFLEN = 64 # Asegúrate que esta es la longitud del derived key en bytes

def verificar_contrasena_scrypt(contrasena_ingresada_str, hash_almacenado_str):
    """
    Verifica una contraseña ingresada contra un hash almacenado en el formato
    scrypt:N:r:p$salt_base64$derived_key_hex
    """
    if not hash_almacenado_str or not isinstance(hash_almacenado_str, str) or '$' not in hash_almacenado_str:
        print(f"Hash almacenado parece inválido o no es el formato esperado: {hash_almacenado_str}")
        return False
    try:
        parts = hash_almacenado_str.split('$')
        if len(parts) != 3:
            print(f"Formato de hash incorrecto (no 3 partes): {hash_almacenado_str}")
            return False

        param_str, salt_b64_str, stored_derived_key_hex = parts

        algo_param_parts = param_str.split(':')
        if len(algo_param_parts) != 4 or algo_param_parts[0].lower() != 'scrypt':
            print(f"Formato de hash incorrecto (sección de params): {param_str}")
            return False

        N = int(algo_param_parts[1])
        r = int(algo_param_parts[2])
        p = int(algo_param_parts[3])

        salt_bytes = base64.b64decode(salt_b64_str)

        nuevo_hash_derivado_bytes = scrypt.hash(
            contrasena_ingresada_str.encode('utf-8'),
            salt_bytes,
            N=N,
            r=r,
            p=p,
            buflen=SCRYPT_VERIFY_BUFLEN
        )
        nuevo_hash_derivado_hex = nuevo_hash_derivado_bytes.hex()

        # Comparación segura (aunque para scrypt el timing es menos crítico)
        # Usaremos una comparación simple por ahora, pero hmac.compare_digest es más robusto
        # import hmac
        # return hmac.compare_digest(nuevo_hash_derivado_hex.encode('ascii'), stored_derived_key_hex.encode('ascii'))
        if nuevo_hash_derivado_hex == stored_derived_key_hex:
            return True
        else:
            # print(f"Debug: Hashes no coinciden. Calculado: {nuevo_hash_derivado_hex}, Almacenado: {stored_derived_key_hex}")
            return False

    except Exception as e:
        print(f"Error durante la verificación de contraseña: {e} (Hash: {hash_almacenado_str})")
        return False




@login_bp.route('/registrar_nuevo_usuario', methods=['POST'])
def registrar_nuevo_usuario():
    """Ruta para registrar un nuevo usuario en el sistema."""
    datos = request.get_json()
    nombre = datos.get('nombre').strip()
    email = datos.get('email').strip()
    contrasena_texto_plano = datos.get('contrasena').strip()
    id_perfil = datos.get('id_perfil', 2) # Asigna un perfil por defecto (ej. 'Usuario Estándar')

    if not nombre or not email or not contrasena_texto_plano:
        return jsonify({"status": "error", "mensaje": "Todos los campos son obligatorios."}), 400

    if len(contrasena_texto_plano) < 8:
        return jsonify({"status": "error", "mensaje": "La contraseña debe tener al menos 8 caracteres."}), 400

    hashed_password = generate_password_hash(contrasena_texto_plano)

    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"status": "error", "mensaje": "Error de conexión a la base de datos."}), 500

    cursor = conexion.cursor()
    try:
        # Verifica si el email ya existe para evitar duplicados
        cursor.execute("SELECT COUNT(*) FROM usuario WHERE email = %s", (email,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error", "mensaje": "El email ya está registrado."}), 409

        # Inserta el nuevo usuario con la contraseña hasheada en la columna 'contrasena'
        cursor.execute(
            "INSERT INTO usuario (nombre, email, contrasena, id_perfil) VALUES (%s, %s, %s, %s)",
            (nombre, email, hashed_password, id_perfil)
        )
        conexion.commit()

        registrar_evento(nombre, "Registro de Usuario", f"Nuevo usuario registrado: {email}")
        return jsonify({"status": "success", "mensaje": "Usuario registrado exitosamente."}), 201

    except Exception as e:
        conexion.rollback()
        print(f"Error al registrar nuevo usuario: {e}")
        return jsonify({"status": "error", "mensaje": "Error al registrar el usuario.", "detalle": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@login_bp.route('/crear_perfil', methods=['POST'])
def crear_perfil():
    """Ruta para crear un nuevo perfil/rol en el sistema."""
    datos = request.get_json()
    nombre = datos.get("nombre", "").strip()
    estado = datos.get("estado", "").strip()
    descripcion = datos.get("descripcion", "").strip()

    if not nombre or not estado or not descripcion:
        return jsonify({"status": "error", "mensaje": "❌ Todos los campos son obligatorios."}), 400

    if nombre.isnumeric():
        return jsonify({"status": "error", "mensaje": "❌ El nombre del perfil no puede ser solo números."}), 400

    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Valida que no exista un perfil con el mismo nombre
        cursor.execute("SELECT COUNT(*) as total FROM perfil WHERE LOWER(nombre) = LOWER(%s)", (nombre,))
        if cursor.fetchone()["total"] > 0:
            return jsonify({"status": "error", "mensaje": "❌ Ya existe un perfil con ese nombre."}), 409

        cursor.execute(
            "INSERT INTO perfil (nombre, estado, descripcion) VALUES (%s, %s, %s)",
            (nombre, estado, descripcion)
        )
        conexion.commit()

        registrar_evento(session.get('usuario'), "Creación de perfil", f"Se creó el perfil: {nombre}")
        return jsonify({"status": "success", "mensaje": "✅ Perfil creado correctamente."})
    except Exception as e:
        print("Error al crear perfil:", e)
        return jsonify({"status": "error", "mensaje": "❌ Error al guardar el perfil.", "detalle": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()





@login_bp.route('/perfiles', methods=['GET'])
def obtener_perfiles():
    """Ruta para obtener todos los perfiles existentes."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id_perfil, nombre, estado, descripcion FROM perfil")
        perfiles = cursor.fetchall()
        return jsonify(perfiles), 200
    except Exception as e:
        print("Error al obtener perfiles:", e)
        return jsonify({"status": "error", "mensaje": "❌ No se pudieron cargar los perfiles."}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@login_bp.route('/editar_perfil/<int:id_perfil>', methods=['PUT'])
def editar_perfil(id_perfil):
    """Ruta para editar un perfil existente."""
    datos = request.get_json()
    nombre = datos.get("nombre", "").strip()
    estado = datos.get("estado", "").strip()
    descripcion = datos.get("descripcion", "").strip()

    if not nombre or not estado or not descripcion:
        return jsonify({"status": "error", "mensaje": "❌ Todos los campos son obligatorios."}), 400

    if nombre.isnumeric():
        return jsonify({"status": "error", "mensaje": "❌ El nombre del perfil no puede ser solo números."}), 400

    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Valida nombre duplicado para otro perfil
        cursor.execute("SELECT COUNT(*) as total FROM perfil WHERE LOWER(nombre) = LOWER(%s) AND id_perfil != %s", (nombre, id_perfil))
        if cursor.fetchone()["total"] > 0:
            return jsonify({"status": "error", "mensaje": "❌ Ya existe otro perfil con ese nombre."}), 409

        cursor.execute(
            "UPDATE perfil SET nombre = %s, estado = %s, descripcion = %s WHERE id_perfil = %s",
            (nombre, estado, descripcion, id_perfil)
        )
        conexion.commit()

        registrar_evento(session.get('usuario'), "Actualización de perfil", f"Perfil ID {id_perfil} actualizado")
        return jsonify({"status": "success", "mensaje": "✅ Perfil actualizado correctamente."})
    except Exception as e:
        print("❌ Error al editar perfil:", e)
        return jsonify({"status": "error", "mensaje": "❌ Error al editar el perfil.", "detalle": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@login_bp.route('/inhabilitar_perfil/<int:id_perfil>', methods=['PUT'])
def inhabilitar_perfil(id_perfil):
    """Ruta para inhabilitar un perfil (cambiar su estado a 'inactivo')."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE perfil SET estado = 'inactivo' WHERE id_perfil = %s", (id_perfil,))
        conexion.commit()

        registrar_evento(session.get('usuario'), "Inhabilitación de perfil", f"Se inhabilitó el perfil con ID {id_perfil}")

        return jsonify({"status": "success", "mensaje": "✅ Perfil inhabilitado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": "❌ Error al inhabilitar el perfil.", "detalle": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


from flask import request # Asegúrate de tener request importado

# ... (otros imports)

@login_bp.route('/toggle_perfil_estado/<int:id_perfil>', methods=['PUT'])
def toggle_perfil_estado(id_perfil):
    """Ruta para cambiar el estado de un perfil (activo/inactivo)."""
    datos = request.get_json()
    nuevo_estado = datos.get('estado') # El frontend enviará 'activo' o 'inactivo'

    if nuevo_estado not in ['activo', 'inactivo']:
        return jsonify({"status": "error", "mensaje": "❌ Estado no válido proporcionado."}), 400

    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"status": "error", "mensaje": "🚨 Error de conexión DB."}), 500
    
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE perfil SET estado = %s WHERE id_perfil = %s", (nuevo_estado, id_perfil))
        conexion.commit()

        accion_registrada = "Habilitación" if nuevo_estado == 'activo' else "Inhabilitación"
        # Asumo que tienes 'session' y 'registrar_evento' disponibles
        # from flask import session 
        # from modelo.eventos import registrar_evento (o donde esté)
        if 'usuario' in session:
             user_name = session.get('usuario')
        else:
             user_name = "Sistema" # O algún valor por defecto si no hay sesión

        registrar_evento(user_name, f"{accion_registrada} de perfil", f"Se cambió estado a '{nuevo_estado}' para perfil ID {id_perfil}")
        
        mensaje_exito = f"✅ Perfil puesto como '{nuevo_estado}' correctamente."
        return jsonify({"status": "success", "mensaje": mensaje_exito})
    except Exception as e:
        # from flask import current_app (si quieres usar current_app.logger)
        # current_app.logger.error(f"Error al cambiar estado del perfil {id_perfil}: {e}")
        print(f"Error al cambiar estado del perfil {id_perfil}: {e}") # Log básico si no usas logger
        conexion.rollback()
        return jsonify({"status": "error", "mensaje": "❌ Error al actualizar el estado del perfil.", "detalle": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

        

@login_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Ruta para solicitar el restablecimiento de contraseña (envío de email)."""
    if request.method == 'POST':
        email = request.form.get('email')
        usuario = obtener_usuario_por_email(email)

        if usuario:
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            # Se usa 'id_usuario' del usuario obtenido de la DB para generar el token
            token = serializer.dumps(usuario['id_usuario'], salt='password-reset-salt')

            # Construye la URL completa para el email
            # CORRECCIÓN: Usar 'login.reset_token' para referenciar la ruta del Blueprint 'login'
            reset_url = url_for('login.reset_token', token=token, _external=True)

            try:
                msg = Message("Restablecer tu Contraseña",
                              sender=current_app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[email])
                msg.body = f"""Hola {usuario['email']},

Parece que solicitaste un restablecimiento de contraseña.
Haz clic en el siguiente enlace para establecer una nueva contraseña:

{reset_url}

Este enlace es válido por 1 hora. Si no solicitaste un restablecimiento, por favor ignora este correo.

Saludos,
Tu Equipo de Soporte
"""
                current_app.extensions['mail'].send(msg)
                flash('Se ha enviado un enlace de restablecimiento a tu correo electrónico. Revisa tu bandeja de entrada y spam.', 'info')
                registrar_evento(email, "Solicitud de Restablecimiento de Contraseña", f"Enlace enviado a {email}")
            except Exception as e:
                flash(f'Ocurrió un error al enviar el correo: {e}. Por favor, verifica tu configuración de correo.', 'danger')
                current_app.logger.error(f"Error al enviar email de restablecimiento a {email}: {e}")
                registrar_evento(email, "Error de Envío de Correo de Restablecimiento", f"Error: {e}")
        else:
            # Mensaje genérico por seguridad para no revelar si el email existe o no
            flash('Si el correo electrónico está registrado, se ha enviado un enlace de restablecimiento.', 'info')
            registrar_evento(email, "Intento de Solicitud de Restablecimiento (Email no encontrado o genérico)", "Email no registrado o mensaje genérico para seguridad")

        # Redirige a la misma página para mostrar mensajes flash y evitar reenvío de formulario
        # CORRECCIÓN: Usar 'login.forgot_password' para referenciar la ruta del Blueprint 'login'
        return redirect(url_for('login.forgot_password'))
    return render_template('forgot_password.html')


@login_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """Ruta para restablecer la contraseña usando un token."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    user_id = None
    try:
        # Carga y valida el token. Si expira o es inválido, lanzará una excepción.
        user_id = serializer.loads(token, salt='password-reset-salt', max_age=3600) # Token válido por 1 hora
    except Exception:
        flash('El enlace de restablecimiento es inválido o ha expirado. Por favor, solicita uno nuevo.', 'danger')
        registrar_evento("Desconocido", "Enlace de Restablecimiento Inválido/Expirado", f"Token: {token}")
        # CORRECCIÓN: Usar 'login.forgot_password' para referenciar la ruta del Blueprint 'login'
        return redirect(url_for('login.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validaciones de la nueva contraseña
        if not new_password or not confirm_password:
            flash('Por favor, ingresa y confirma la nueva contraseña.', 'warning')
            return render_template('reset_password.html', token=token)

        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'warning')
            return render_template('reset_password.html', token=token)

        if len(new_password) < 8: # Mínimo 8 caracteres, puedes añadir más reglas (números, símbolos, etc.)
            flash('La contraseña debe tener al menos 8 caracteres.', 'warning')
            return render_template('reset_password.html', token=token)

        hashed_password = generate_password_hash(new_password)

        # Actualiza la contraseña en la base de datos usando el ID del token
        if actualizar_contraseña_usuario(user_id, hashed_password):
            flash('Tu contraseña ha sido restablecida exitosamente. Ahora puedes iniciar sesión.', 'success')
            registrar_evento(f"ID_Usuario:{user_id}", "Contraseña Restablecida Exitosamente", "Contraseña cambiada a través de enlace de recuperación")
            # CORRECCIÓN: Usar 'login.home' para redirigir a la página de login después del éxito
            return redirect(url_for('login.home'))
        else:
            flash('Ocurrió un error al actualizar la contraseña. Inténtalo de nuevo.', 'danger')
            registrar_evento(f"ID_Usuario:{user_id}", "Error al Restablecer Contraseña", "Fallo al actualizar la contraseña en la DB")
            return render_template('reset_password.html', token=token)

    # Renderiza la plantilla de restablecimiento de contraseña para solicitudes GET
    return render_template('reset_password.html', token=token)


# Los siguientes Blueprints están definidos aquí, pero se registran en app.py
# Es una práctica común definirlos en archivos separados. Si ya los tienes en archivos separados,
# esto podría ser duplicado o una convención diferente.
# Si solo son para este archivo, entonces están bien aquí.
sistema_bp = Blueprint('sistema', __name__)

@sistema_bp.route('/estado_sistema')
def estado_sistema():
    """Ruta para obtener el estado del sistema (CPU, memoria, disco)."""
    cpu = psutil.cpu_percent(interval=1)
    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage('/')

    return jsonify({
        'cpu': cpu,
        'memoria_usada': round(memoria.used / (1024 ** 3), 2),
        'memoria_total': round(memoria.total / (1024 ** 3), 2),
        'memoria_porcentaje': memoria.percent,
        'disco_usado': round(disco.used / (1024 ** 3), 2),
        'disco_total': round(disco.total / (1024 ** 3), 2),
        'disco_porcentaje': disco.percent
    })


def obtener_resumen_monitoreo():
    """Obtiene un resumen de los últimos eventos de monitoreo de red."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT iporigen AS ip_origen,
               ipdestino AS ip_destino,
               protocolo,
               puerto_destino,
               fecha_captura AS timestamp
        FROM escanear_red
        ORDER BY fecha_captura DESC
        LIMIT 5
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


@login_bp.route('/api/resumen_monitoreo')
def api_resumen_monitoreo():
    """Endpoint API para obtener el resumen de monitoreo de red."""
    datos = obtener_resumen_monitoreo()
    return jsonify(datos)


eventos_bp = Blueprint('eventos_bp', __name__)

@eventos_bp.route('/eventos_recientes')
def eventos_recientes():
    """Endpoint API para obtener los eventos más recientes."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT usuario, descripcion, tipo_evento, fecha_evento FROM eventos ORDER BY fecha_evento DESC LIMIT 10")
        eventos = cursor.fetchall()
        return jsonify(eventos)
    except Exception as e:
        print("❌ Error al obtener eventos:", e)
        return jsonify([]), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@login_bp.route('/alertas')
def alertas():
    """Ruta para la página de alertas."""
    return render_template('alertas.html', alertas=obtener_alertas())


@login_bp.route('/api/alertas')
def api_alertas():
    """Endpoint API para obtener todas las alertas en formato JSON."""
    try:
        alertas_data = obtener_alertas()

        return jsonify(alertas_data)

    except Exception as e:
        print(f"❌ Error al obtener alertas para API: {e}")
        return jsonify({"status": "error", "mensaje": "No se pudieron cargar las alertas.", "detalle": str(e)}), 500


@login_bp.route('/usuarios')
def gestion_usuarios():
    """Ruta para la gestión de usuarios (requiere perfil de administrador)."""
    if 'perfil' not in session or session['perfil'] != 1: # 1 es el id de perfil para 'Administrador'
        flash("Usted no tiene permiso para acceder aquí.")
        # CORRECCIÓN: Usar 'login.dashboard' para redirigir al dashboard
        return redirect(url_for('login.dashboard'))
    return render_template('usuarios.html')


@login_bp.route('/usuarios/perfil-actual')
def perfil_actual():
    """Endpoint API para obtener el perfil actual del usuario logueado."""
    perfil = session.get('perfil', 'Invitado')
    return jsonify({'perfil': perfil})

@login_bp.route('/editar_perfil/<int:id>', methods=['PUT'], endpoint='editar_perfil_admin')
def editar_perfil_admin(id):
    """Ruta para editar perfil de usuario (lógica para administradores)."""
    pass

@login_bp.route('/editar_perfil_usuario/<int:id>', methods=['PUT'], endpoint='editar_perfil_usuario')
def editar_perfil_usuario(id):
    """Ruta para editar perfil de usuario (lógica para usuarios)."""
    pass

@login_bp.route('/perfiles')
def listar_perfiles():
    """Ruta para listar perfiles (requiere perfil de administrador)."""
    if 'perfil' not in session or session['perfil'] != 1: # 1 = Administrador
        return jsonify({'error': 'No autorizado'}), 403

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id_perfil, nombre, estado, descripcion FROM perfil")
        perfiles = cursor.fetchall()
        return jsonify(perfiles), 200
    except Exception as e:
        print("Error al obtener perfiles:", e)
        return jsonify({"status": "error", "mensaje": "❌ No se pudieron cargar los perfiles."}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@login_bp.route('/ultimas-amenazas')
def ultimas_amenazas():
    """Endpoint API para obtener las últimas amenazas de seguridad."""
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT tipo, nivel, descripcion, ip_origen, fecha FROM eventos_seguridad ORDER BY fecha DESC LIMIT 5")
        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        print(f"❌ Error al obtener últimas amenazas: {e}")
        return jsonify({"status": "error", "mensaje": "No se pudieron cargar las últimas amenazas.", "detalle": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()






