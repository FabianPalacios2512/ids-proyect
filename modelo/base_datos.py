import mysql.connector


def obtener_conexion():
    """Establece la conexión con la base de datos MariaDB."""
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="ids_proyect"
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None


def obtener_perfiles():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_perfil, nombre AS descripcion, estado FROM perfil")
    perfiles = cursor.fetchall()
    conexion.close()
    return perfiles

def crear_perfil(nombre, estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO perfil (nombre, estado) VALUES (%s, %s)", (nombre, estado))
    conexion.commit()
    conexion.close()

def contar_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuario")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def contar_dispositivos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM dispositivos")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def obtener_eventos():
    try:
        conn = obtener_conexion()  # Usando la misma función para obtener la conexión
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM eventos_seguridad")
        eventos = cursor.fetchall()
        conn.close()
        return eventos
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    
def obtener_ultimos_eventos(limit=2):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM eventos_seguridad ORDER BY fecha DESC LIMIT %s", (limit,))
        eventos = cursor.fetchall()
        conn.close()
        return eventos
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []


def obtener_alertas():
    conn = obtener_conexion()  # Usando la misma función para obtener la conexión
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM eventos_seguridad"  # Aquí también estamos asumiendo que las alertas están en esta tabla
    cursor.execute(query)
    alertas = cursor.fetchall()
    cursor.close()
    conn.close()
    return alertas


import mysql.connector




def obtener_perfiles():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_perfil, nombre AS descripcion, estado FROM perfil")
    perfiles = cursor.fetchall()
    conexion.close()
    return perfiles

def crear_perfil(nombre, estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO perfil (nombre, estado) VALUES (%s, %s)", (nombre, estado))
    conexion.commit()
    conexion.close()

def contar_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuario")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def contar_dispositivos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM dispositivos")
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0]

def obtener_eventos():
    try:
        conn = obtener_conexion()  # Usando la misma función para obtener la conexión
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM eventos_seguridad")
        eventos = cursor.fetchall()
        conn.close()
        return eventos
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    
def obtener_ultimos_eventos(limit=2):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM eventos_seguridad ORDER BY fecha DESC LIMIT %s", (limit,))
        eventos = cursor.fetchall()
        conn.close()
        return eventos
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []


def obtener_alertas():
    conn = obtener_conexion()  # Usando la misma función para obtener la conexión
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM eventos_seguridad"  # Aquí también estamos asumiendo que las alertas están en esta tabla
    cursor.execute(query)
    alertas = cursor.fetchall()
    cursor.close()
    conn.close()
    return alertas


def obtener_alertas_nuevas():
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM eventos_seguridad WHERE estado_alerta = 'nueva' ORDER BY fecha DESC")
    alertas_nuevas = cursor.fetchall()
    cursor.close()
    conn.close()
    return alertas_nuevas




# Prueba de conexión
if __name__ == "__main__":
    conexion = obtener_conexion()
    if conexion:
        print("✅ Conexión exitosa a MariaDB")
        conexion.close()
    else:
        print("❌ No se pudo conectar a la base de datos")




# Prueba de conexión
if __name__ == "__main__":
    conexion = obtener_conexion()
    if conexion:
        print("✅ Conexión exitosa a MariaDB")
        conexion.close()
    else:
        print("❌ No se pudo conectar a la base de datos")
