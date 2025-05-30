# En tu archivo modelo/base_datos.py

import mysql.connector
# import logging # Descomenta si decides usar logging en lugar de print para los errores
# logger = logging.getLogger(__name__)

# --- Configuración de la base de datos (ajusta si es necesario) ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234", # ¡Asegúrate de que esta sea la contraseña correcta!
    "database": "ids_proyect"
}

def obtener_conexion():
    """
    Establece y retorna una conexión a la base de datos.
    Maneja excepciones en caso de fallo de conexión.
    """
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        # print("ℹ️ Conexión a BD establecida.") # Log opcional para depuración
        return conexion
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar a la base de datos: {err}") # Considera logger.error()
        return None

def _ejecutar_consulta_y_cerrar(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Función auxiliar para ejecutar consultas SQL, manejar la conexión/cursor
    y cerrar recursos de manera segura.
    """
    conexion = obtener_conexion()
    if not conexion:
        return None if (fetch_one or fetch_all) else False

    cursor = None
    try:
        # --- MODIFICACIÓN IMPORTANTE AQUÍ ---
        # Usamos dictionary=True para devolver resultados como diccionarios.
        # Usamos buffered=True para evitar errores de "Unread result found".
        cursor = conexion.cursor(dictionary=True, buffered=True)
        # --- FIN DE LA MODIFICACIÓN ---
        
        # print(f"ℹ️ Ejecutando Query: {query} con Params: {params}") # Log opcional
        cursor.execute(query, params)

        if commit:
            conexion.commit()
            # print("ℹ️ Commit realizado.") # Log opcional
            return True
        elif fetch_one:
            resultado = cursor.fetchone()
            # print(f"ℹ️ Fetch one resultado: {resultado}") # Log opcional
            return resultado # Esto retorna un diccionario o None
        elif fetch_all:
            resultados = cursor.fetchall()
            # print(f"ℹ️ Fetch all resultados: {len(resultados) if resultados else 0} filas.") # Log opcional
            return resultados
        return True # Para operaciones que solo ejecutan (ej. DDL sin commit explícito necesario aquí)

    except mysql.connector.Error as err:
        print(f"❌ Error en la consulta de la base de datos: {query} - {err}") # Considera logger.error()
        if commit and conexion: # Solo hacer rollback si era una operación de escritura que falló
            try:
                conexion.rollback()
                # print("ℹ️ Rollback realizado.") # Log opcional
            except mysql.connector.Error as rb_err:
                print(f"❌ Error durante el rollback: {rb_err}") # Considera logger.error()
        return None if (fetch_one or fetch_all) else False
    finally:
        if cursor:
            try:
                cursor.close()
            except mysql.connector.Error as cur_err:
                print(f"❌ Error cerrando cursor: {cur_err}") # Considera logger.warning()
        if conexion and conexion.is_connected():
            try:
                conexion.close()
                # print("ℹ️ Conexión a BD cerrada.") # Log opcional
            except mysql.connector.Error as conn_err:
                print(f"❌ Error cerrando conexión: {conn_err}") # Considera logger.warning()

# --- Funciones que utilizan el helper _ejecutar_consulta_y_cerrar ---

def obtener_perfiles():
    """Obtiene todos los perfiles de la base de datos."""
    query = "SELECT id_perfil, nombre AS descripcion, estado FROM perfil"
    return _ejecutar_consulta_y_cerrar(query, fetch_all=True)

def crear_perfil(nombre, estado, descripcion):
    """Crea un nuevo perfil en la base de datos."""
    query = "INSERT INTO perfil (nombre, estado, descripcion) VALUES (%s, %s, %s)"
    return _ejecutar_consulta_y_cerrar(query, (nombre, estado, descripcion), commit=True)

def contar_usuarios():
    """Cuenta el total de usuarios en la base de datos."""
    query = "SELECT COUNT(*) FROM usuario"
    resultado = _ejecutar_consulta_y_cerrar(query, fetch_one=True)
    # Acceder por la clave 'COUNT(*)' ya que el cursor es dictionary=True
    return resultado.get('COUNT(*)', 0) if resultado else 0

def contar_dispositivos():
    """Cuenta el total de dispositivos en la base de datos."""
    query = "SELECT COUNT(*) FROM dispositivos"
    resultado = _ejecutar_consulta_y_cerrar(query, fetch_one=True)
    # Acceder por la clave 'COUNT(*)' ya que el cursor es dictionary=True
    return resultado.get('COUNT(*)', 0) if resultado else 0

# Estas funciones de eventos estaban en tu versión. Si no usas 'eventos_bp',
# podrías eliminarlas si no son llamadas desde otros módulos (ej. alertas_acciones_bp).
def obtener_eventos():
    """Obtiene todos los eventos de seguridad."""
    query = "SELECT * FROM eventos_seguridad"
    return _ejecutar_consulta_y_cerrar(query, fetch_all=True)

def obtener_ultimos_eventos(limit=5): # Ajustado el límite por defecto como ejemplo
    """Obtiene los últimos N eventos de seguridad."""
    query = "SELECT * FROM eventos_seguridad ORDER BY fecha DESC LIMIT %s"
    return _ejecutar_consulta_y_cerrar(query, (limit,), fetch_all=True)

def obtener_alertas(): # Esta función parece redundante si eventos_seguridad contiene las alertas
    """Obtiene todas las alertas de seguridad (asume que están en eventos_seguridad)."""
    query = "SELECT * FROM eventos_seguridad ORDER BY fecha DESC"
    return _ejecutar_consulta_y_cerrar(query, fetch_all=True)

def obtener_alertas_nuevas():
    """Obtiene las alertas de seguridad con estado 'nueva'."""
    query = "SELECT * FROM eventos_seguridad WHERE estado_alerta = 'nueva' ORDER BY fecha DESC"
    return _ejecutar_consulta_y_cerrar(query, fetch_all=True)

def obtener_usuario_por_email(email):
    """
    Busca un usuario en la tabla 'usuario' por su email.
    Retorna el usuario como un diccionario o None si no se encuentra.
    """
    query = "SELECT id_usuario, email, contrasena, id_perfil FROM usuario WHERE email = %s" # Asumiendo que quieres id_perfil también
    return _ejecutar_consulta_y_cerrar(query, (email,), fetch_one=True)

def actualizar_contraseña_usuario(user_id, hashed_password):
    """
    Actualiza la contraseña de un usuario en la tabla 'usuario'.
    Retorna True si la actualización fue exitosa, False en caso contrario.
    """
    query = "UPDATE usuario SET contrasena = %s WHERE id_usuario = %s"
    return _ejecutar_consulta_y_cerrar(query, (hashed_password, user_id), commit=True)

# --- Funciones que podrías necesitar para alertas_acciones_controlador.py ---
# (Asegúrate de que estas funciones existan si son llamadas desde otros módulos)

def obtener_estado_bloqueado_dispositivo(target_ip): # Ejemplo de cómo se llamaría la función que faltaba
    """Consulta el estado 'bloqueado' de un dispositivo específico."""
    query = "SELECT bloqueado FROM dispositivos WHERE direccion_ip = %s"
    resultado = _ejecutar_consulta_y_cerrar(query, (target_ip,), fetch_one=True)
    if resultado:
        return resultado.get('bloqueado') # Devuelve 0, 1, o None si la columna no existe
    return None # IP no encontrada o error

def actualizar_estado_bloqueo_dispositivo(target_ip, nuevo_estado_int):
    """Actualiza el estado 'bloqueado' de un dispositivo."""
    query = "UPDATE dispositivos SET bloqueado = %s WHERE direccion_ip = %s"
    # Verificar si la operación fue exitosa (afectó filas o el estado ya era el deseado)
    success = _ejecutar_consulta_y_cerrar(query, (nuevo_estado_int, target_ip), commit=True)
    if success:
        # Adicionalmente, podrías verificar si el estado realmente es el nuevo_estado_int
        # llamando a obtener_estado_bloqueado_dispositivo, pero commit=True ya da una buena indicación.
        current_status = obtener_estado_bloqueado_dispositivo(target_ip)
        return current_status == nuevo_estado_int
    return False


# Prueba de conexión y funciones (opcional, puedes quitarla)
if __name__ == "__main__":
    print("Probando la conexión a la base de datos...")
    conexion_test = obtener_conexion()
    if conexion_test:
        print("✅ Conexión exitosa a MariaDB")
        
        print("\nProbando obtener_perfiles():")
        perfiles = obtener_perfiles()
        if perfiles is not None:
            print(f"Perfiles encontrados: {len(perfiles)}")
            # for perfil in perfiles:
            # print(perfil)
        else:
            print("No se pudieron obtener perfiles o no hay perfiles.")

        # print("\nProbando contar_usuarios():")
        # num_usuarios = contar_usuarios()
        # print(f"Número total de usuarios: {num_usuarios}")

        # print("\nProbando obtener_usuario_por_email('test@example.com'):")
        # usuario = obtener_usuario_por_email('test@example.com')
        # if usuario:
        # print(f"Usuario encontrado: {usuario}")
        # else:
        # print("Usuario no encontrado o error.")
            
        conexion_test.close()
        print("\n✅ Conexión de prueba cerrada.")
    else:
        print("❌ No se pudo conectar a la base de datos para las pruebas.")