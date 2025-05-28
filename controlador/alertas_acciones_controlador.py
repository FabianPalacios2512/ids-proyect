# controlador/alertas_acciones_controlador.py
from flask import Blueprint, jsonify, request, send_file
import logging
import io # Para manejar el archivo en memoria
import time # Importado
import traceback # Importado
from docx import Document # Necesitas: pip install python-docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Asumiendo que tienes estos módulos y funciones
try:
    from controlador.arp_manager import start_full_attack, stop_full_attack, get_mac_for_ipv4, mac_to_ipv6_linklocal, GATEWAY_IPV6_LL
    from controlador.iptables_manager import block_ipv4, unblock_ipv4, block_ipv6, unblock_ipv6
    from modelo.base_datos import obtener_conexion # Para actualizar estado bloqueado
    ATTACK_AVAILABLE = True
    logging.info("✅ Módulos de ataque y DB cargados para acciones de alerta.")
except ImportError as e:
    logging.error(f"⚠️ ADVERTENCIA en alertas_acciones: No se pudo importar un módulo ({e}). Funciones limitadas.")
    ATTACK_AVAILABLE = False
    # Funciones Dummy para que la app no se caiga
    start_full_attack = stop_full_attack = lambda ip: False
    get_mac_for_ipv4 = lambda ip: None # <-- CORREGIDO: get_mac_for_ipv4 necesita un argumento
    mac_to_ipv6_linklocal = lambda mac: None
    GATEWAY_IPV6_LL = None
    block_ipv4 = unblock_ipv4 = block_ipv6 = unblock_ipv6 = lambda ip: False
    obtener_conexion = lambda: None


alertas_acciones_bp = Blueprint('alertas_acciones', __name__, url_prefix='/alerta')

def actualizar_estado_bloqueado_db(target_ip, bloqueado_status):
    """Actualiza el estado 'bloqueado' en la tabla dispositivos."""
    if not obtener_conexion:
        logging.warning(f"DB_UPDATE: No se puede actualizar estado para {target_ip}, conexión a DB no disponible.")
        return False
    conexion = obtener_conexion()
    if not conexion:
        logging.error(f"DB_UPDATE: No se pudo obtener conexión para actualizar {target_ip}")
        return False
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id FROM dispositivos WHERE direccion_ip = %s", (target_ip,))
        dispositivo_existente = cursor.fetchone()

        if dispositivo_existente:
            logging.info(f"DB_UPDATE: Actualizando estado bloqueado a {bloqueado_status} para IP {target_ip}")
            cursor.execute("UPDATE dispositivos SET bloqueado = %s WHERE direccion_ip = %s", (bloqueado_status, target_ip))
            conexion.commit()
            logging.info(f"DB_UPDATE: Estado de {target_ip} actualizado a {bloqueado_status}.")
            return True
        else:
            logging.info(f"DB_UPDATE: Dispositivo con IP {target_ip} no encontrado en la tabla 'dispositivos'. No se actualizó estado.")
            return False
    except Exception as e:
        logging.error(f"DB_UPDATE: Error al actualizar estado bloqueado para {target_ip}: {e}")
        if conexion and conexion.is_connected():
            conexion.rollback()
        return False
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

@alertas_acciones_bp.route('/bloquear_ip/<path:target_ip>', methods=['POST'])
def bloquear_ip_desde_alerta(target_ip):
    # <<< INICIO FIX: Verificación robusta de la IP recibida >>>
    if not target_ip or target_ip.strip().lower() == 'null' or target_ip.strip().lower() == 'none' or target_ip.strip() == '':
        logging.error(f"ALERTA_ACCION: Se recibió una IP inválida o nula: '{target_ip}'")
        return jsonify({"mensaje": f"❌ Se recibió una IP inválida o nula ('{target_ip}'). No se puede bloquear."}), 400
    # <<< FIN FIX >>>

    logging.info(f"ALERTA_ACCION: Solicitud de bloqueo para IP: {target_ip}")

    if not ATTACK_AVAILABLE:
        return jsonify({"mensaje": "❌ Funcionalidad de ataque no disponible en el servidor."}), 503

    # <<< INICIO FIX: Verificar MAC antes de bloquear >>>
    target_mac = get_mac_for_ipv4(target_ip)
    if not target_mac:
        # Se agrega el log de error que ya tenías en la consola, pero ahora devuelve una respuesta clara.
        logging.error(f"No se pudo obtener MAC para {target_ip}. No se puede iniciar ataque completo.")
        return jsonify({"mensaje": f"❌ No se pudo obtener la MAC para {target_ip}. ¿Está el dispositivo en línea y en la misma red?"}), 500
    # <<< FIN FIX >>>

    if not start_full_attack(target_ip):
        logging.error(f"ALERTA_ACCION: Fallo al iniciar MiTM para {target_ip}.")
        return jsonify({"mensaje": f"❌ No se pudo iniciar MiTM para {target_ip}. Revisa logs del servidor."}), 500

    ipv4_blocked = block_ipv4(target_ip)
    ipv6_blocked = False
    # target_mac = get_mac_for_ipv4(target_ip) # Ya lo obtuvimos arriba
    target_ipv6_ll = None
    if target_mac and GATEWAY_IPV6_LL:
        target_ipv6_ll = mac_to_ipv6_linklocal(target_mac)
        if target_ipv6_ll:
            logging.info(f"ALERTA_ACCION: Intentando bloqueo IPv6 para {target_ipv6_ll} (derivado de {target_ip})")
            ipv6_blocked = block_ipv6(target_ipv6_ll)
        else:
            logging.warning(f"ALERTA_ACCION: No se pudo derivar IPv6 LL para MAC {target_mac} de IP {target_ip}")
    else:
        logging.warning(f"ALERTA_ACCION: No se bloqueará IPv6 para {target_ip} (Falta MAC o Gateway IPv6_LL no disponible).")

    if not ipv4_blocked and not ipv6_blocked:
        logging.error(f"ALERTA_ACCION: Falló el bloqueo (IPv4 e IPv6) para {target_ip}. Deteniendo MiTM.")
        stop_full_attack(target_ip)
        return jsonify({"mensaje": f"❌ Falló el bloqueo (IPv4/IPv6) para {target_ip}. Firewall podría no estar respondiendo."}), 500

    db_updated = actualizar_estado_bloqueado_db(target_ip, 1)

    msg = f"Proceso de bloqueo para {target_ip} iniciado."
    if ipv4_blocked: msg += " (IPv4 ✓)"
    else: msg += " (IPv4 ✗)"
    if ipv6_blocked: msg += " (IPv6 ✓)"
    elif GATEWAY_IPV6_LL and target_mac: msg += " (IPv6 ✗)"

    if not db_updated:
        msg += " [Error al actualizar DB]"
    logging.info(f"ALERTA_ACCION: {msg}")
    return jsonify({"mensaje": msg }), 200


@alertas_acciones_bp.route('/generar_informe', methods=['POST'])
def generar_informe_alerta_docx():
    try:
        alerta_data = request.json
        if not alerta_data:
            return jsonify({"mensaje": "No se recibieron datos de la alerta."}), 400

        document = Document()
        document.add_heading('Informe de Alerta de Seguridad', level=1)

        p = document.add_paragraph()
        p.add_run('Fecha del Informe: ').bold = True
        p.add_run(time.strftime("%Y-%m-%d %H:%M:%S"))

        def add_data_row(label, value):
            p = document.add_paragraph()
            p.add_run(f"{label}: ").bold = True
            p.add_run(str(value) if value is not None else 'N/A')

        add_data_row('ID Alerta (si disponible)', alerta_data.get('id_alerta', alerta_data.get('id')))
        add_data_row('Tipo de Alerta', alerta_data.get('tipo'))
        add_data_row('Nivel de Severidad', alerta_data.get('nivel'))
        add_data_row('Fecha de Detección', alerta_data.get('fecha'))
        add_data_row('Repeticiones', alerta_data.get('repeticiones'))
        document.add_heading('Descripción de la Amenaza', level=2)
        document.add_paragraph(str(alerta_data.get('descripcion', 'N/A')))

        document.add_heading('Detalles de Red', level=2)
        add_data_row('IP Origen', alerta_data.get('ip_origen'))
        add_data_row('MAC Origen', alerta_data.get('mac_origen'))
        add_data_row('Puerto Origen', alerta_data.get('puerto_origen'))
        add_data_row('SO Origen', alerta_data.get('so_origen'))
        add_data_row('IP Destino', alerta_data.get('ip_destino'))
        add_data_row('MAC Destino', alerta_data.get('mac_destino'))
        add_data_row('Puerto Destino', alerta_data.get('puerto_destino'))
        add_data_row('Protocolo', alerta_data.get('protocolo'))
        document.add_heading('Estado del Evento', level=2)
        add_data_row('Estado de la Alerta (en IDS)', alerta_data.get('estado_alerta'))
        add_data_row('Estado del Evento Original', alerta_data.get('estado_evento'))
        file_stream = io.BytesIO()
        document.save(file_stream)
        file_stream.seek(0)

        filename = f"informe_alerta_{alerta_data.get('tipo', 'generico').replace(' ', '_')}_{time.strftime('%Y%m%d%H%M%S')}.docx"
        logging.info(f"ALERTA_ACCION: Generando informe DOCX: {filename}")
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logging.error(f"ALERTA_ACCION: Error al generar informe DOCX: {e}")
        logging.error(traceback.format_exc())
        return jsonify({"mensaje": "Error interno al generar el informe."}), 500