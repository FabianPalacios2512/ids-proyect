from flask import Blueprint, render_template, request, jsonify
from modelo.base_datos import obtener_conexion
import threading
from controlador.escaneo_dispositivos import iniciar_escaneo_red, detener_escaneo_red
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



#configuracion de adactavilidad del panel 

paquetes_bp = Blueprint('paquetes', __name__)

captura_proceso = None
escaneo_en_progreso = False
login_bp = Blueprint('login', __name__, template_folder="../vista")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))





@paquetes_bp.route('/estado_escaneo')
def estado_escaneo():
    global escaneo_en_progreso
    return jsonify({"en_progreso": escaneo_en_progreso})

@paquetes_bp.route('/obtener_paquetes', methods=['GET'])
def obtener_paquetes():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id_paquete, ip_origen, ip_destino, mac_origen, mac_destino, puerto_origen, puerto_destino, protocolo, tamano, fecha_captura, ttl FROM paquetes ORDER BY fecha_captura DESC LIMIT 100")
        paquetes = cursor.fetchall()
        return jsonify(paquetes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()


@paquetes_bp.route('/datos_red')
def datos_red():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM escanear_red ORDER BY fecha_captura DESC LIMIT 50")
        datos = cursor.fetchall()
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": "No se pudieron obtener los datos", "detalle": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()



@paquetes_bp.route('/iniciar_captura', methods=['POST'])
def iniciar_captura():
    global captura_proceso
    if captura_proceso is None:
        try:
            captura_proceso = subprocess.Popen(['sudo', '/home/kali/Descargas/venv/bin/python3', 'controlador/captura_paquetes.py'])
            return jsonify({"status": "success", "mensaje": "✅ Captura iniciada."}), 200
        except Exception as e:
            return jsonify({"status": "error", "mensaje": "❌ Error al iniciar la captura.", "detalle": str(e)}), 500
    else:
        return jsonify({"status": "error", "mensaje": "⚠️ La captura ya está en ejecución."}), 400

@paquetes_bp.route('/detener_captura', methods=['POST'])
def detener_captura():
    global captura_proceso
    if captura_proceso is not None:
        captura_proceso.terminate()
        captura_proceso = None
        return jsonify({"status": "success", "mensaje": "🛑 Captura detenida."}), 200
    else:
        return jsonify({"status": "error", "mensaje": "⚠️ No hay una captura en ejecución."}), 400
