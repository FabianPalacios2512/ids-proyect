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
from modelo.base_datos import obtener_conexion

import threading

detener_evento = threading.Event()

dispositivos_bp = Blueprint('dispositivos', __name__)
escaneo_en_progreso = False

#ver datos de los dispositivos 
@dispositivos_bp.route('/datos_dispositivos')
def datos_dispositivos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM dispositivos ORDER BY fecha_escaneo DESC LIMIT 50")
        datos = cursor.fetchall()
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": "No se pudieron obtener los datos", "detalle": str(e)}), 500
    finally:
        cursor.close()
        conexion.close()

# CAPTURA PARA LOS DISPOSITIVOS 

@dispositivos_bp.route('/dispositivos')
def dispositivos():
    return render_template("dispositivos.html")

@dispositivos_bp.route('/iniciar_escaneo_dispositivos', methods=['POST'])
def ruta_iniciar_escaneo_dispositivos():
    global escaneo_en_progreso
    try:
        escaneo_en_progreso = True
        hilo = threading.Thread(target=iniciar_escaneo_red)
        hilo.start()
        return jsonify({"status": "success", "mensaje": "✅ Escaneo de dispositivos iniciado."}), 200
    except Exception as e:
        escaneo_en_progreso = False
        return jsonify({"status": "error", "mensaje": "❌ Error al iniciar escaneo.", "detalle": str(e)}), 500


@dispositivos_bp.route('/detener_escaneo_dispositivos', methods=['POST'])
def ruta_detener_escaneo_dispositivos():
    global escaneo_en_progreso
    try:
        detener_escaneo_red()
        escaneo_en_progreso = False
        return jsonify({"status": "success", "mensaje": "🛑 Escaneo detenido correctamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": "❌ Error al detener escaneo.", "detalle": str(e)}), 500


@dispositivos_bp.route('/desconectar_dispositivo/<ip>', methods=['POST'])
def desconectar_dispositivo(ip):
    # lógica para desconectar el dispositivo de la red
    return jsonify({"mensaje": f"Dispositivo {ip} desconectado correctamente"})
