from flask import Blueprint, render_template, request, jsonify
from modelo.base_datos import obtener_conexion
from modelo.eventos import registrar_evento
from flask import session

usuarios_bp = Blueprint('usuarios', __name__)


@usuarios_bp.route('/usuarios')
def vista_usuarios():
    return render_template('usuarios.html')

@usuarios_bp.route('/usuarios/perfiles')
def listar_perfiles():
    conexion = obtener_conexion()
    with conexion.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id_perfil, nombre FROM perfil WHERE estado = 'activo'")
        perfiles = cursor.fetchall()
    conexion.close()
    return jsonify(perfiles)

@usuarios_bp.route('/usuarios/listar')
def listar_usuarios():
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id_usuario, u.nombre, u.apellido, u.email, u.telefono,
               p.nombre AS perfil, u.estado
        FROM usuario u
        JOIN perfil p ON u.id_perfil = p.id_perfil
    """)
    usuarios = cursor.fetchall()
    conn.close()
    return jsonify(usuarios)


@usuarios_bp.route('/usuarios/obtener/<int:id_usuario>')
def obtener_usuario(id_usuario):
    conexion = obtener_conexion()
    with conexion.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
    conexion.close()
    return jsonify(usuario)

@usuarios_bp.route('/usuarios/crear', methods=['POST'])
def crear_usuario():
    datos = request.get_json()
    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        try:
            cursor.execute("""
                INSERT INTO usuario (nombre, apellido, telefono, email, contrasena, id_perfil, estado)
                VALUES (%s, %s, %s, %s, %s, %s, 'activo')
            """, (datos['nombre'], datos['apellido'], datos['telefono'],
                  datos['email'], datos['contrasena'], datos['id_perfil']))
            conexion.commit()

            # Evento registrado
            registrar_evento(session.get('usuario'), "Creación de usuario", f"Se creó el usuario: {datos['nombre']} {datos['apellido']}")

            return jsonify({'mensaje': 'Usuario creado correctamente.', 'exito': True})
        except Exception as e:
            return jsonify({'mensaje': f'Error al crear el usuario: {str(e)}', 'exito': False})
        finally:
            conexion.close()



@usuarios_bp.route('/usuarios/actualizar/<int:id_usuario>', methods=['PUT'])
def actualizar_usuario(id_usuario):
    datos = request.get_json()
    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        try:
            cursor.execute("""
                UPDATE usuario SET nombre=%s, apellido=%s, telefono=%s,
                email=%s, contrasena=%s, id_perfil=%s
                WHERE id_usuario=%s
            """, (datos['nombre'], datos['apellido'], datos['telefono'],
                  datos['email'], datos['contrasena'], datos['id_perfil'], id_usuario))
            conexion.commit()

            # Registrar evento
            from modelo.eventos import registrar_evento
            from flask import session
            registrar_evento(session.get('usuario'), "Actualización de usuario", f"Actualizó al usuario con ID: {id_usuario}")

            return jsonify({'mensaje': 'Usuario actualizado.', 'exito': True})
        except Exception as e:
            print("Error al actualizar usuario:", e)
            return jsonify({'mensaje': 'Error al actualizar.', 'exito': False})
        finally:
            conexion.close()


@usuarios_bp.route('/usuarios/eliminar/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        try:
            cursor.execute("UPDATE usuario SET estado='inactivo' WHERE id_usuario=%s", (id_usuario,))
            conexion.commit()

            # Registrar evento
            from modelo.eventos import registrar_evento
            from flask import session
            registrar_evento(session.get('usuario'), "Eliminación de usuario", f"Se inhabilitó el usuario con ID: {id_usuario}")

            return jsonify({'mensaje': 'Usuario eliminado.', 'exito': True})
        except Exception as e:
            print("Error al eliminar usuario:", e)
            return jsonify({'mensaje': 'Error al eliminar.', 'exito': False})
        finally:
            conexion.close()



