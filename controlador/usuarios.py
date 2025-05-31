# (Keep all other imports and blueprint setup the same)
import scrypt
import os
import base64
from flask import Blueprint, render_template, request, jsonify, session
from modelo.base_datos import obtener_conexion
from modelo.eventos import registrar_evento

usuarios_bp = Blueprint('usuarios', __name__)

SCRYPT_N = 32768
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_BUFLEN = 64
SALT_BYTES = 12

# ... (verificar_email_existente, vista_usuarios, listar_perfiles, listar_usuarios, obtener_usuario functions remain the same) ...
@usuarios_bp.route('/usuarios/verificar-email', methods=['GET'])
def verificar_email_existente():
    email_a_verificar = request.args.get('email')

    if not email_a_verificar:
        return jsonify({'error': 'Parámetro email requerido.', 'existe': False}), 400

    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id_usuario FROM usuario WHERE email = %s", (email_a_verificar,))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                return jsonify({'existe': True, 'usuarioId': usuario_existente['id_usuario']})
            else:
                return jsonify({'existe': False})

    except Exception as e:
        print(f"Error al verificar email en la base de datos: {e}")
        return jsonify({'error': 'Error interno del servidor al verificar el email.', 'existe': False}), 500
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@usuarios_bp.route('/usuarios')
def vista_usuarios():
    return render_template('usuarios.html')

@usuarios_bp.route('/usuarios/perfiles')
def listar_perfiles():
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id_perfil, nombre FROM perfil WHERE estado = 'activo'")
            perfiles = cursor.fetchall()
        return jsonify(perfiles)
    except Exception as e:
        print(f"Error al listar perfiles: {e}")
        return jsonify({'error': 'Error al listar perfiles.'}), 500
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@usuarios_bp.route('/usuarios/listar')
def listar_usuarios():
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.email, u.telefono,
            p.nombre AS perfil, u.estado
            FROM usuario u
            JOIN perfil p ON u.id_perfil = p.id_perfil
        """)
        usuarios = cursor.fetchall()
        return jsonify(usuarios)
    except Exception as e:
        print(f"Error al listar usuarios: {e}")
        return jsonify({'error': 'Error al listar usuarios.'}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@usuarios_bp.route('/usuarios/obtener/<int:id_usuario>')
def obtener_usuario(id_usuario):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id_usuario, nombre, apellido, telefono, email, id_perfil, estado FROM usuario WHERE id_usuario = %s", (id_usuario,))
            usuario = cursor.fetchone()
        if usuario:
            return jsonify(usuario)
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return jsonify({'error': 'Error al obtener usuario.'}), 500
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@usuarios_bp.route('/usuarios/crear', methods=['POST'])
def crear_usuario():
    datos = request.get_json()
    conexion = None
    try:
        contrasena_plain = datos.get('contrasena')
        if not contrasena_plain:
            return jsonify({'mensaje': 'La contraseña es requerida.', 'exito': False}), 400

        salt_bytes = os.urandom(SALT_BYTES)
        derived_key_bytes = scrypt.hash(
            contrasena_plain.encode('utf-8'), salt_bytes,
            N=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, buflen=SCRYPT_BUFLEN
        )
        salt_b64 = base64.b64encode(salt_bytes).decode('ascii')
        derived_key_hex = derived_key_bytes.hex()
        contrasena_string = f"scrypt:{SCRYPT_N}:{SCRYPT_R}:{SCRYPT_P}${salt_b64}${derived_key_hex}"

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO usuario (nombre, apellido, telefono, email, contrasena, id_perfil, estado, salt_contrasena)
                VALUES (%s, %s, %s, %s, %s, %s, 'activo', %s)
            """, (datos['nombre'], datos['apellido'], datos['telefono'],
                  datos['email'], contrasena_string, datos['id_perfil'], '')) # CHANGED None to ''
            conexion.commit()

        registrar_evento(session.get('usuario_id'), "Creación de usuario", f"Se creó el usuario: {datos['nombre']} {datos['apellido']}")
        return jsonify({'mensaje': 'Usuario creado correctamente.', 'exito': True})

    except scrypt.error as se:
        print(f"Error de Scrypt al crear usuario: {se}")
        return jsonify({'mensaje': 'Error de seguridad al procesar la contraseña.', 'exito': False}), 500
    except Exception as e:
        if "Duplicate entry" in str(e) and "for key 'email'" in str(e):
             return jsonify({'mensaje': 'Error al crear el usuario: El correo electrónico ya existe.', 'exito': False}), 409
        print(f"Error al crear el usuario: {e}")
        return jsonify({'mensaje': f'Error al crear el usuario: {str(e)}', 'exito': False}), 500
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@usuarios_bp.route('/usuarios/actualizar/<int:id_usuario>', methods=['PUT'])
def actualizar_usuario(id_usuario):
    datos = request.get_json()
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            update_fields = []
            update_values = []

            if 'nombre' in datos:
                update_fields.append("nombre=%s")
                update_values.append(datos['nombre'])
            if 'apellido' in datos:
                update_fields.append("apellido=%s")
                update_values.append(datos['apellido'])
            if 'telefono' in datos:
                update_fields.append("telefono=%s")
                update_values.append(datos['telefono'])
            if 'email' in datos:
                update_fields.append("email=%s")
                update_values.append(datos['email'])
            if 'id_perfil' in datos:
                update_fields.append("id_perfil=%s")
                update_values.append(datos['id_perfil'])
            if 'estado' in datos:
                update_fields.append("estado=%s")
                update_values.append(datos['estado'])

            contrasena_plain = datos.get('contrasena')
            if contrasena_plain:
                salt_bytes = os.urandom(SALT_BYTES)
                derived_key_bytes = scrypt.hash(
                    contrasena_plain.encode('utf-8'), salt_bytes,
                    N=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, buflen=SCRYPT_BUFLEN
                )
                salt_b64 = base64.b64encode(salt_bytes).decode('ascii')
                derived_key_hex = derived_key_bytes.hex()
                contrasena_string = f"scrypt:{SCRYPT_N}:{SCRYPT_R}:{SCRYPT_P}${salt_b64}${derived_key_hex}"

                update_fields.append("contrasena=%s")
                update_values.append(contrasena_string)
                update_fields.append("salt_contrasena=%s")
                update_values.append('') # CHANGED None to ''

            if not update_fields:
                return jsonify({'mensaje': 'No hay datos para actualizar.', 'exito': False}), 400

            query = f"UPDATE usuario SET {', '.join(update_fields)} WHERE id_usuario=%s"
            update_values.append(id_usuario)
            cursor.execute(query, tuple(update_values))
            conexion.commit()

        registrar_evento(session.get('usuario_id'), "Actualización de usuario", f"Actualizó al usuario con ID: {id_usuario}")
        return jsonify({'mensaje': 'Usuario actualizado.', 'exito': True})

    except scrypt.error as se:
        print(f"Error de Scrypt al actualizar usuario: {se}")
        return jsonify({'mensaje': 'Error de seguridad al procesar la contraseña.', 'exito': False}), 500
    except Exception as e:
        if "Duplicate entry" in str(e) and "for key 'email'" in str(e):
             return jsonify({'mensaje': 'Error al actualizar: El correo electrónico ya está en uso por otro usuario.', 'exito': False}), 409
        # Check for the specific "cannot be null" error for salt_contrasena
        if "1048" in str(e) and "Column 'salt_contrasena' cannot be null" in str(e):
            print(f"Error al actualizar usuario (salt_contrasena NOT NULL constraint): {e}")
            return jsonify({'mensaje': "Error interno: restricción de base de datos en 'salt_contrasena'.", 'exito': False}), 500
        print(f"Error al actualizar usuario: {e}")
        return jsonify({'mensaje': f'Error al actualizar: {str(e)}', 'exito': False}), 500
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

# ... (eliminar_usuario function remains the same) ...
@usuarios_bp.route('/usuarios/eliminar/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # En lugar de borrar, se cambia el estado a 'inactivo'
            cursor.execute("UPDATE usuario SET estado='inactivo' WHERE id_usuario=%s", (id_usuario,))
            conexion.commit()

        registrar_evento(session.get('usuario_id'), "Eliminación de usuario", f"Se inhabilitó el usuario con ID: {id_usuario}")

        return jsonify({'mensaje': 'Usuario inhabilitado correctamente.', 'exito': True})
    except Exception as e:
        print(f"Error al inhabilitar usuario: {e}")
        return jsonify({'mensaje': 'Error al inhabilitar el usuario.', 'exito': False}), 500
    finally:
        if conexion and conexion.is_connected():
            conexion.close()