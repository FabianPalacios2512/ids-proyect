from datetime import datetime
from modelo.base_datos import obtener_conexion

def registrar_evento(usuario, descripcion, tipo_evento="Acción del sistema"):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO eventos (usuario, descripcion, tipo_evento, fecha_evento)
            VALUES (%s, %s, %s, %s)
        """, (usuario, descripcion, tipo_evento, datetime.now()))
        conexion.commit()
    except Exception as e:
        print("⚠️ Error al registrar evento:", e)
    finally:
        cursor.close()
        conexion.close()
