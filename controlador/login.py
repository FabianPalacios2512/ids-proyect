from flask import Blueprint, request, jsonify, render_template
import sys
import os
import subprocess
import threading
import time
from modelo.base_datos import obtener_conexion
from modelo import base_datos
from flask import Blueprint, jsonify
from modelo.base_datos import obtener_conexion
from flask import jsonify
from flask import Blueprint, jsonify
from modelo.base_datos import obtener_conexion
from flask import Blueprint, jsonify
import psutil
from flask import jsonify
from flask import session
from modelo.eventos import registrar_evento




login_bp = Blueprint('login', __name__, template_folder="../vista")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modelo.base_datos import contar_usuarios, contar_dispositivos

@login_bp.route('/')
def home():
    return render_template("login.html")

from flask import render_template, session, redirect, url_for
from modelo.base_datos import contar_usuarios, contar_dispositivos, obtener_eventos

from modelo.base_datos import obtener_ultimos_eventos


@login_bp.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login.home'))

    total_usuarios = contar_usuarios()
    total_dispositivos = contar_dispositivos()
    resumen_monitoreo = obtener_eventos()  # Esto sigue trayendo todo, por si lo usas en alguna parte

    # Trae solo los 2 eventos más recientes
    ultimos_eventos = obtener_ultimos_eventos()

    # Trae todas las alertas
    alertas = obtener_alertas()

    return render_template('dashboard.html',
                           usuario=session['usuario'],
                           total_usuarios=total_usuarios,
                           total_dispositivos=total_dispositivos,
                           resumen_monitoreo=resumen_monitoreo,
                           ultimos_eventos=ultimos_eventos,
                           alertas=alertas)  # Pasa las alertas al template






@login_bp.route('/dashboard_admin')
def dashboard_admin():
    return render_template('dashboard_admin.html')

from flask import session, redirect, url_for
@login_bp.route('/logout')
def logout():
    usuario = session.get('usuario')  # Obtenemos el usuario antes de borrar la sesión
    if usuario:
        registrar_evento(usuario, "Logout", "Cierre de sesión")  # Registramos el evento
    session.clear()  # Limpiamos toda la sesión
    return redirect(url_for('login.home'))  # Redirige al login

@login_bp.route('/monitoreo')
def monitoreo():
    return render_template("monitoreoRed.html")

@login_bp.route('/usuario')
def usuario():
    return render_template("usuario.html")

@login_bp.route('/perfil')
def perfil():
    return render_template("perfil.html")






# CONFIGURACION DEL LOGIN
@login_bp.route('/login', methods=['POST'])
def login():
    datos = request.json
    email = datos.get('email')
    contrasena = datos.get('contrasena')

    if not email or not contrasena:
        return jsonify({"status": "error", "mensaje": "⚠️ Por favor, completa todos los campos."}), 400

    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"status": "error", "mensaje": "🚨 Error en el sistema. No se pudo conectar a la base de datos."}), 500

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM usuario WHERE email = %s AND contrasena = %s", (email, contrasena))
        usuario = cursor.fetchone()

        if usuario:
            session['usuario'] = usuario['nombre']
            session['perfil'] = usuario['id_perfil']  # Almacena el perfil en la sesión
            
            # Registrar evento de inicio de sesión
            registrar_evento(usuario['nombre'], "Inicio de sesión")

            return jsonify({
                "status": "success",
                "mensaje": f"✅ Bienvenido {usuario['nombre']} 🎉",
                "usuario": usuario['nombre']
            }), 200
        else:
            return jsonify({"status": "error", "mensaje": "❌ Credenciales incorrectas."}), 401

    except Exception as e:
        print("Error al iniciar sesión:", e)  # Esto lo imprime en la terminal
        return jsonify({
            "status": "error",
            "mensaje": "⚠️ Ocurrió un problema inesperado.",
            "detalle": str(e)
        }), 500

    finally:
        cursor.close()
        conexion.close()


@login_bp.route('/crear_perfil', methods=['POST'])
def crear_perfil():
    from modelo.eventos import registrar_evento
    from flask import session

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

        # Validar duplicado
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
        cursor.close()
        conexion.close()


login = Blueprint('login', __name__)

@login_bp.route('/perfiles', methods=['GET'])
def obtener_perfiles():
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
        cursor.close()
        conexion.close()


@login_bp.route('/editar_perfil/<int:id_perfil>', methods=['PUT'])
def editar_perfil(id_perfil):
    from modelo.eventos import registrar_evento
    from flask import session

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

        # Validar nombre duplicado para otro perfil
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
        cursor.close()
        conexion.close()



@login_bp.route('/inhabilitar_perfil/<int:id_perfil>', methods=['PUT'])
def inhabilitar_perfil(id_perfil):
    from modelo.eventos import registrar_evento
    from flask import session

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE perfil SET estado = 'inactivo' WHERE id_perfil = %s", (id_perfil,))
        conexion.commit()

        # Registrar evento
        registrar_evento(session.get('usuario'), "Inhabilitación de perfil", f"Se inhabilitó el perfil con ID {id_perfil}")

        return jsonify({"status": "success", "mensaje": "✅ Perfil inhabilitado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": "❌ Error al inhabilitar el perfil.", "detalle": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()



#contenido del dasboar 



sistema_bp = Blueprint('sistema', __name__)

@sistema_bp.route('/estado_sistema')
def estado_sistema():
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


from modelo.base_datos import obtener_conexion
def obtener_resumen_monitoreo():
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
    datos = obtener_resumen_monitoreo()
    return jsonify(datos)


#contro de eventos

from modelo.eventos import registrar_evento

from flask import Blueprint, jsonify
from modelo.base_datos import obtener_conexion

eventos_bp = Blueprint('eventos_bp', __name__)

@eventos_bp.route('/eventos_recientes')
def eventos_recientes():
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
        cursor.close()
        conexion.close()



from flask import Flask, render_template
from modelo.base_datos import obtener_alertas  # Asegúrate de tener esta función

app = Flask(__name__)

@login_bp.route('/alertas')
def alertas():
    # Tu código para la vista de alertas
    return render_template('alertas.html', alertas=obtener_alertas())





from flask import session, redirect, url_for, flash, render_template, jsonify

@login_bp.route('/usuarios')
def gestion_usuarios():
    # Verificamos si el perfil del usuario está en la sesión y si es 'Administrador'
    if 'perfil' not in session or session['perfil'] != 1:  # 1 es el id de perfil para 'Administrador'
        flash("Usted no tiene permiso para acceder aquí.")
        return redirect(url_for('login.dashboard'))  # Redirige al dashboard o a donde desees
    return render_template('usuarios.html')


# Ruta para obtener el perfil actual del usuario
@login_bp.route('/usuarios/perfil-actual')
def perfil_actual():
    # Obtenemos el perfil del usuario desde la sesión
    perfil = session.get('perfil', 'Invitado')  # Si no está en la sesión, asignamos 'Invitado'
    # Retornamos el perfil como respuesta en formato JSON
    return jsonify({'perfil': perfil})

@login_bp.route('/editar_perfil/<int:id>', methods=['PUT'], endpoint='editar_perfil_admin')
def editar_perfil_admin(id):
    # lógica de edición para administradores
    pass

@login_bp.route('/editar_perfil_usuario/<int:id>', methods=['PUT'], endpoint='editar_perfil_usuario')
def editar_perfil_usuario(id):
    # lógica de edición para usuarios
    pass

@login_bp.route('/perfiles')
def listar_perfiles():
    if 'perfil' not in session or session['perfil'] != 1:  # 1 = Administrador
        return jsonify({'error': 'No autorizado'}), 403

    # Código que devuelve los perfiles




#consultar por imaill 



@login_bp.route('/ultimas-amenazas')
def ultimas_amenazas():
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT tipo, nivel, descripcion, ip_origen, fecha FROM eventos_seguridad ORDER BY fecha DESC LIMIT 5")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)