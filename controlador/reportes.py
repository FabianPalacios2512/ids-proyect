from flask import Blueprint, jsonify, Response
import mysql.connector
from datetime import datetime
import csv
import io

# Importa tu función para obtener la conexión (ajusta la ruta si es necesario)
from modelo.base_datos import obtener_conexion 

# Define el Blueprint
reportes_bp = Blueprint('reportes_bp', __name__)

# --- FUNCIONES AUXILIARES ---

# En controlador/reportes.py
from flask import Blueprint, render_template
# ... (tus otras importaciones para este archivo: Response, csv, io, obtener_conexion, etc.) ...

reportes_bp = Blueprint('reportes_bp', __name__, template_folder='../vista') # Asegúrate que template_folder sea correcto si el HTML está allí

# ... (todas tus rutas @reportes_bp.route('/api/reportes/...') para JSON y descarga CSV) ...

# ESTA ES LA FUNCIÓN IMPORTANTE PARA LA PÁGINA DE REPORTES
@reportes_bp.route('/dashboard') # Esta es la URL, por ejemplo /reportes/dashboard
def mostrar_dashboard_reportes(): # Este es el nombre de la función (endpoint)
    # Aquí renderizas el HTML que hicimos para el dashboard de reportes
    # (el que tiene las pestañas y llama al JavaScript para cargar datos)
    return render_template('reporte_con_tabs.html') # O como hayas llamado a ese archivo HTML

def format_datetime(obj):
    """Función auxiliar para formatear fechas para JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Si no es datetime, simplemente lo devuelve (para CSV) o lanza error (para JSON si es necesario)
    # Para CSV, es mejor devolver el valor o 'N/A'
    return obj if obj is not None else 'N/A'
    # Si quieres que sea estricto para JSON y falle si no es datetime:
    # raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def generate_csv_response(data, headers, filename):
    """Función auxiliar para generar la respuesta CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir cabecera (keys del diccionario de headers)
    writer.writerow(headers.keys())

    # Escribir datos
    for row in data:
        writer.writerow([
            # Usamos format_datetime para manejar fechas, pero devolvemos 'N/A' para None
            format_datetime(row.get(key)) if isinstance(row.get(key), datetime) else row.get(key, 'N/A') 
            for key in headers.values() # Itera sobre los nombres de columna de la DB
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# --- RUTAS API JSON (PARA EL FRONTEND) ---

@reportes_bp.route('/api/reportes/threat_types')
def get_threat_types():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT tipo, COUNT(*) as count FROM eventos_seguridad WHERE tipo IS NOT NULL AND tipo != '' GROUP BY tipo ORDER BY count DESC;"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@reportes_bp.route('/api/reportes/chronological')
def get_chronological_events():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT fecha, tipo, ip_origen, ip_destino, nivel, descripcion FROM eventos_seguridad ORDER BY fecha DESC LIMIT 50;"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        for row in data: row['fecha'] = format_datetime(row.get('fecha'))
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@reportes_bp.route('/api/reportes/suspicious_ips')
def get_suspicious_ips():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT ip_origen, COUNT(*) as count, MAX(fecha) as last_seen FROM eventos_seguridad WHERE ip_origen IS NOT NULL AND ip_origen != '' GROUP BY ip_origen ORDER BY count DESC LIMIT 50;"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        for row in data: row['last_seen'] = format_datetime(row.get('last_seen'))
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@reportes_bp.route('/api/reportes/vulnerable_devices')
def get_vulnerable_devices():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT ip_destino, COUNT(*) as count, MAX(fecha) as last_seen, MAX(tipo) as common_attack FROM eventos_seguridad WHERE ip_destino IS NOT NULL AND ip_destino != '' GROUP BY ip_destino ORDER BY count DESC LIMIT 50;"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        for row in data: row['last_seen'] = format_datetime(row.get('last_seen'))
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@reportes_bp.route('/api/reportes/summary_stats')
def get_summary_stats():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_alerts FROM eventos_seguridad WHERE fecha >= NOW() - INTERVAL 1 DAY")
        total_alerts = cursor.fetchone()['total_alerts']
        cursor.execute("SELECT tipo FROM eventos_seguridad WHERE tipo IS NOT NULL AND tipo != '' GROUP BY tipo ORDER BY COUNT(*) DESC LIMIT 1")
        top_threat = (cursor.fetchone() or {}).get('tipo', 'N/A')
        cursor.execute("SELECT ip_origen FROM eventos_seguridad WHERE ip_origen IS NOT NULL AND ip_origen != '' GROUP BY ip_origen ORDER BY COUNT(*) DESC LIMIT 1")
        top_ip = (cursor.fetchone() or {}).get('ip_origen', 'N/A')
        cursor.execute("SELECT ip_destino FROM eventos_seguridad WHERE ip_destino IS NOT NULL AND ip_destino != '' GROUP BY ip_destino ORDER BY COUNT(*) DESC LIMIT 1")
        top_device = (cursor.fetchone() or {}).get('ip_destino', 'N/A')
        cursor.execute("SELECT nivel, COUNT(*) as count FROM eventos_seguridad GROUP BY nivel")
        severity_counts = cursor.fetchall()
        conn.close()
        return jsonify({
            "total_alerts_24h": total_alerts, "top_threat": top_threat,
            "top_attacker_ip": top_ip, "top_target_device": top_device,
            "severity_counts": severity_counts
        })
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@reportes_bp.route('/api/reportes/events_by_severity/<nivel>')
def get_events_by_severity(nivel):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        if nivel.upper() == 'N/A' or nivel.upper() == 'NULL':
            query = "SELECT fecha, tipo, ip_origen, ip_destino, descripcion FROM eventos_seguridad WHERE nivel IS NULL OR nivel = '' ORDER BY fecha DESC LIMIT 100;"
            cursor.execute(query)
        else:
            query = "SELECT fecha, tipo, ip_origen, ip_destino, descripcion FROM eventos_seguridad WHERE nivel = %s ORDER BY fecha DESC LIMIT 100;"
            cursor.execute(query, (nivel,))
        data = cursor.fetchall()
        conn.close()
        for row in data: row['fecha'] = format_datetime(row.get('fecha'))
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@reportes_bp.route('/api/reportes/events_by_type/<tipo>')
def get_events_by_type(tipo):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT fecha, ip_origen, ip_destino, nivel, descripcion FROM eventos_seguridad WHERE tipo = %s ORDER BY fecha DESC LIMIT 100;"
        cursor.execute(query, (tipo,))
        data = cursor.fetchall()
        conn.close()
        for row in data: row['fecha'] = format_datetime(row.get('fecha'))
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# --- RUTAS DE DESCARGA CSV ---

@reportes_bp.route('/api/reportes/download/threat_types')
def download_threat_types():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT tipo, COUNT(*) as count FROM eventos_seguridad WHERE tipo IS NOT NULL AND tipo != '' GROUP BY tipo ORDER BY count DESC;"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        headers = {'Tipo de Amenaza': 'tipo', 'Cantidad': 'count'}
        return generate_csv_response(data, headers, "resumen_tipos_amenaza.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reportes_bp.route('/api/reportes/download/chronological')
def download_chronological():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT fecha, tipo, ip_origen, ip_destino, nivel, descripcion FROM eventos_seguridad ORDER BY fecha DESC;"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        headers = {'Fecha': 'fecha', 'Tipo': 'tipo', 'IP Origen': 'ip_origen', 'IP Destino': 'ip_destino', 'Nivel': 'nivel', 'Descripción': 'descripcion'}
        return generate_csv_response(data, headers, "todos_eventos_cronologicos.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reportes_bp.route('/api/reportes/download/suspicious_ips')
def download_suspicious_ips():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                e.ip_origen, COUNT(*) as count, MAX(e.fecha) as last_seen,
                (SELECT tipo FROM eventos_seguridad WHERE ip_origen = e.ip_origen GROUP BY tipo ORDER BY COUNT(*) DESC LIMIT 1) as common_attack,
                (SELECT ip_destino FROM eventos_seguridad WHERE ip_origen = e.ip_origen GROUP BY ip_destino ORDER BY COUNT(*) DESC LIMIT 1) as top_target
            FROM eventos_seguridad e WHERE e.ip_origen IS NOT NULL AND e.ip_origen != ''
            GROUP BY e.ip_origen ORDER BY count DESC;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        headers = {'IP Atacante': 'ip_origen', 'Total Alertas': 'count', 'Último Evento': 'last_seen', 'Ataque Común': 'common_attack', 'Objetivo Frecuente': 'top_target'}
        return generate_csv_response(data, headers, "ips_sospechosas_detallado.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reportes_bp.route('/api/reportes/download/vulnerable_devices')
def download_vulnerable_devices():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                e.ip_destino, COUNT(*) as count, MAX(e.fecha) as last_seen, MAX(e.tipo) as common_attack,
                (SELECT ip_origen FROM eventos_seguridad WHERE ip_destino = e.ip_destino GROUP BY ip_origen ORDER BY COUNT(*) DESC LIMIT 1) as top_source
            FROM eventos_seguridad e WHERE e.ip_destino IS NOT NULL AND e.ip_destino != ''
            GROUP BY e.ip_destino ORDER BY count DESC;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        headers = {'IP Interna': 'ip_destino', 'Total Alertas': 'count', 'Último Evento': 'last_seen', 'Ataque Común': 'common_attack', 'Atacante Frecuente': 'top_source'}
        return generate_csv_response(data, headers, "dispositivos_vulnerables_detallado.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reportes_bp.route('/api/reportes/download/events_by_severity/<nivel>')
def download_events_by_severity(nivel):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        if nivel.upper() == 'N/A' or nivel.upper() == 'NULL':
            query = "SELECT fecha, tipo, ip_origen, ip_destino, descripcion FROM eventos_seguridad WHERE nivel IS NULL OR nivel = '' ORDER BY fecha DESC;"
            cursor.execute(query)
        else:
            query = "SELECT fecha, tipo, ip_origen, ip_destino, descripcion FROM eventos_seguridad WHERE nivel = %s ORDER BY fecha DESC;"
            cursor.execute(query, (nivel,))
        data = cursor.fetchall()
        conn.close()
        headers = {'Fecha': 'fecha', 'Tipo': 'tipo', 'IP Origen': 'ip_origen', 'IP Destino': 'ip_destino', 'Descripción': 'descripcion'}
        return generate_csv_response(data, headers, f"eventos_severidad_{nivel}.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reportes_bp.route('/api/reportes/download/events_by_type/<tipo>')
def download_events_by_type(tipo):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT fecha, ip_origen, ip_destino, nivel, descripcion FROM eventos_seguridad WHERE tipo = %s ORDER BY fecha DESC;"
        cursor.execute(query, (tipo,))
        data = cursor.fetchall()
        conn.close()
        headers = {'Fecha': 'fecha', 'IP Origen': 'ip_origen', 'IP Destino': 'ip_destino', 'Nivel': 'nivel', 'Descripción': 'descripcion'}
        safe_tipo = "".join(c for c in tipo if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
        return generate_csv_response(data, headers, f"eventos_tipo_{safe_tipo}.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500