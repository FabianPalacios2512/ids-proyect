from flask import Blueprint, render_template, request, jsonify
from modelo.base_datos import obtener_conexion
import threading
import logging

# --- IMPORTACIÓN DE CONTROLADORES ---
# Importamos el escaneo de red
try:
    from controlador.escaneo_dispositivos import iniciar_escaneo_red, detener_escaneo_red
    SCAN_AVAILABLE = True
    logging.info("✅ Módulo escaneo_dispositivos cargado.")
except ImportError as e:
    logging.error(f"❌ ERROR CRÍTICO: No se pudo importar escaneo_dispositivos ({e}). El escaneo no funcionará.")
    # Funciones Dummy para escaneo si falla la importación
    iniciar_escaneo_red = lambda: logging.error("ESCANEADO NO DISPONIBLE")
    detener_escaneo_red = lambda: logging.error("ESCANEADO NO DISPONIBLE")
    SCAN_AVAILABLE = False

# Importamos las funciones de ataque y utilidades
try:
    from controlador.arp_manager import (
        start_full_attack,
        stop_full_attack,
        get_mac_for_ipv4,
        mac_to_ipv6_linklocal,
        GATEWAY_IPV6_LL
    )
    from controlador.iptables_manager import (
        block_ipv4,
        unblock_ipv4,
        block_ipv6,
        unblock_ipv6
    )
    ATTACK_AVAILABLE = True
    logging.info("✅ Módulos arp_manager e iptables_manager cargados correctamente.")
except ImportError as e:
    logging.warning(f"⚠️ ADVERTENCIA: No se pudo importar un módulo de ataque ({e}). Funciones de bloqueo no disponibles.")
    # Funciones Dummy para ataque si falla la importación
    start_full_attack = stop_full_attack = lambda ip: False
    get_mac_for_ipv4 = lambda ip: None
    mac_to_ipv6_linklocal = lambda mac: None
    GATEWAY_IPV6_LL = None
    block_ipv4 = unblock_ipv4 = block_ipv6 = unblock_ipv6 = lambda ip: False
    ATTACK_AVAILABLE = False

# --- CONFIGURACIÓN DEL BLUEPRINT Y GLOBALES ---
dispositivos_bp = Blueprint('dispositivos', __name__)
escaneo_en_progreso = False
lock_escaneo = threading.Lock() # Lock para gestionar el acceso a la variable global

# --- FUNCIÓN WORKER PARA EL HILO DE ESCANEO ---
def worker_escaneo():
    """
    Ejecuta el escaneo en segundo plano y actualiza la bandera
    global 'escaneo_en_progreso' al finalizar, usando un Lock.
    """
    global escaneo_en_progreso
    logging.info("WORKER: El hilo de escaneo ha comenzado.")
    try:
        # Ejecutamos la función de escaneo real
        iniciar_escaneo_red()
        logging.info("WORKER: iniciar_escaneo_red ha finalizado con éxito.")
    except Exception as e:
        logging.error(f"WORKER: Ocurrió un error durante iniciar_escaneo_red: {e}")
    finally:
        # Aseguramos que la bandera se ponga en False SIEMPRE al terminar
        with lock_escaneo:
            escaneo_en_progreso = False
        logging.info("WORKER: La bandera escaneo_en_progreso se ha puesto en False.")

# --- RUTAS PARA LA PÁGINA Y DATOS ---
@dispositivos_bp.route('/dispositivos')
def dispositivos():
    """Renderiza la plantilla HTML principal de dispositivos."""
    return render_template("dispositivos.html")

@dispositivos_bp.route('/datos_dispositivos')
def datos_dispositivos():
    """Obtiene los datos de los dispositivos desde la BD y los devuelve como JSON."""
    conexion = None  # Inicializar fuera del try
    cursor = None    # Inicializar fuera del try
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, direccion_ip, direccion_mac, nombre_host, sistema_operativo, puerto, fecha_escaneo, estado_dispositivo, bloqueado FROM dispositivos ORDER BY id DESC LIMIT 100") # O usa fecha_escaneo si prefieres
        datos = cursor.fetchall()
        for d in datos:
            d['bloqueado'] = int(d['bloqueado']) if d.get('bloqueado') is not None else 0
        return jsonify(datos)
    except Exception as e:
        logging.error(f"Error al obtener datos de dispositivos: {e}")
        return jsonify({"error": "No se pudieron obtener los datos", "detalle": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()

# --- RUTAS PARA EL ESCANEO DE RED ---
@dispositivos_bp.route('/iniciar_escaneo_dispositivos', methods=['POST'])
def ruta_iniciar_escaneo_dispositivos():
    """Inicia el escaneo de red en un hilo separado."""
    global escaneo_en_progreso

    if not SCAN_AVAILABLE:
         return jsonify({"status": "error", "mensaje": "❌ Módulo de escaneo no disponible."}), 503

    with lock_escaneo:
        if escaneo_en_progreso:
            return jsonify({"status": "warning", "mensaje": "⚠️ Ya hay un escaneo en progreso."}), 409

        logging.info("Ruta: Iniciando escaneo de red...")
        escaneo_en_progreso = True
        # Usamos worker_escaneo como target del hilo
        hilo = threading.Thread(target=worker_escaneo, daemon=True)
        hilo.start()

    return jsonify({"status": "success", "mensaje": "✅ Escaneo de dispositivos iniciado."}), 200

@dispositivos_bp.route('/detener_escaneo_dispositivos', methods=['POST'])
def ruta_detener_escaneo_dispositivos():
    """Detiene el escaneo de red."""
    global escaneo_en_progreso

    if not SCAN_AVAILABLE:
         return jsonify({"status": "error", "mensaje": "❌ Módulo de escaneo no disponible."}), 503

    with lock_escaneo:
        if not escaneo_en_progreso:
            return jsonify({"status": "warning", "mensaje": "⚠️ No hay ningún escaneo activo para detener."}), 409

        logging.info("Ruta: Deteniendo escaneo de red...")
        detener_escaneo_red()
        # Forzamos la bandera a False aquí también, por si acaso.
        escaneo_en_progreso = False

    return jsonify({"status": "success", "mensaje": "🛑 Escaneo detenido correctamente."}), 200

@dispositivos_bp.route('/estado_escaneo')
def estado_escaneo():
    """Devuelve si hay un escaneo en progreso."""
    global escaneo_en_progreso
    with lock_escaneo:
        return jsonify({"en_progreso": escaneo_en_progreso})

# --- RUTAS DE BLOQUEO/DESBLOQUEO ---
@dispositivos_bp.route('/desconectar_dispositivo/<target_ipv4>', methods=['POST'])
def desconectar_dispositivo_ruta(target_ipv4):
    logging.info(f"FLASK: Intentando desconectar full (IPv4/IPv6) el dispositivo {target_ipv4}")
    if not ATTACK_AVAILABLE:
        logging.error("FLASK: Módulo de ataque no disponible para desconectar.")
        return jsonify({"mensaje": "❌ Módulo de ataque no disponible."}), 503

    if not start_full_attack(target_ipv4):
        logging.error(f"FLASK: No se pudo iniciar MiTM para {target_ipv4}.")
        return jsonify({"mensaje": f"❌ No se pudo iniciar MiTM para {target_ipv4}. Revisa logs."}), 500

    ipv4_blocked = block_ipv4(target_ipv4)
    ipv6_blocked = False
    target_ipv6_ll = None
    target_mac = get_mac_for_ipv4(target_ipv4)

    if target_mac and GATEWAY_IPV6_LL:
        target_ipv6_ll = mac_to_ipv6_linklocal(target_mac)
        if target_ipv6_ll:
            logging.info(f"FLASK: Intentando bloqueo IPv6 Link-Local {target_ipv6_ll}")
            ipv6_blocked = block_ipv6(target_ipv6_ll)
            if not ipv6_blocked: logging.warning(f"FLASK: Falló bloqueo IPv6 para {target_ipv6_ll}.")
        else: logging.warning(f"FLASK: No se pudo derivar IPv6 LL para {target_mac}")
    elif target_mac:
        logging.info(f"FLASK: No se intentará bloqueo IPv6 para {target_ipv4} (Gateway IPv6 no detectado).")
    else:
        logging.warning(f"FLASK: No se pudo obtener MAC para {target_ipv4}, no se bloqueará IPv6.")

    if not ipv4_blocked and not ipv6_blocked:
        logging.error(f"FLASK: Falló bloqueo IPv4 y IPv6 para {target_ipv4}. Deteniendo MiTM.")
        stop_full_attack(target_ipv4)
        return jsonify({"mensaje": f"❌ Falló el bloqueo (IPv4/IPv6) para {target_ipv4}. Revisa logs."}), 500

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("UPDATE dispositivos SET bloqueado = 1 WHERE direccion_ip = %s", (target_ipv4,))
        conexion.commit()
        msg = f"✅ Dispositivo {target_ipv4} proceso de bloqueo iniciado."
        if ipv4_blocked: msg += " (IPv4)"
        if ipv6_blocked: msg += " (IPv6)"
        logging.info(f"FLASK: {msg} y DB actualizada.")
        return jsonify({"mensaje": msg }), 200
    except Exception as e:
        logging.error(f"FLASK: Error en DB al bloquear {target_ipv4}: {e}. Revirtiendo...")
        if ipv4_blocked: unblock_ipv4(target_ipv4)
        if ipv6_blocked and target_ipv6_ll: unblock_ipv6(target_ipv6_ll)
        stop_full_attack(target_ipv4)
        return jsonify({"mensaje": f"❌ Error en DB al bloquear {target_ipv4}.", "detalle": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()

@dispositivos_bp.route('/reconectar_dispositivo/<target_ipv4>', methods=['POST'])
def reconectar_dispositivo_ruta(target_ipv4):
    logging.info(f"FLASK: Intentando reconectar full (IPv4/IPv6) el dispositivo {target_ipv4}")
    if not ATTACK_AVAILABLE:
        logging.error("FLASK: Módulo de ataque no disponible para reconectar.")
        return jsonify({"mensaje": "❌ Módulo de ataque no disponible."}), 503

    unblock_ipv4(target_ipv4)
    target_mac = get_mac_for_ipv4(target_ipv4)
    if target_mac and GATEWAY_IPV6_LL:
        target_ipv6_ll = mac_to_ipv6_linklocal(target_mac)
        if target_ipv6_ll:
            unblock_ipv6(target_ipv6_ll)

    mitm_stopped = stop_full_attack(target_ipv4)

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("UPDATE dispositivos SET bloqueado = 0 WHERE direccion_ip = %s", (target_ipv4,))
        conexion.commit()
        logging.info(f"FLASK: Dispositivo {target_ipv4} reconectado y DB actualizada.")
        return jsonify({"mensaje": f"✅ Dispositivo {target_ipv4} reconectado."}), 200
    except Exception as e:
        logging.error(f"FLASK: Error en DB al reconectar {target_ipv4}: {e}")
        return jsonify({"mensaje": f"❌ Error en DB al reconectar {target_ipv4}.", "detalle": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()