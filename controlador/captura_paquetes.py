from scapy.all import sniff, IP, TCP, UDP, Ether, ICMP
import mariadb
import threading
import time
import sys
import socket
from datetime import datetime, timedelta
from collections import defaultdict, deque

# ========================
# 🔌 CONEXIÓN A MARIADB
# ========================
def conectar_db():
    try:
        conn = mariadb.connect(
            host="localhost", 
            user="root",      
            password="1234",  
            database="ids_proyect", 
            autocommit=True   
        )
        return conn
    except mariadb.Error as e:
        print(f"[❌] Error conectando a MariaDB: {e}.")
        return None

# ========================
# ⚙️ VARIABLES GLOBALES Y CONFIGURACIÓN
# ========================
buffer_lock = threading.Lock()
paquetes_buffer_crudos = [] # Buffer para la tabla 'escanear_red'
eventos_recientes_lock = threading.Lock()
eventos_recientes_detalle = defaultdict(lambda: datetime.min)

BATCH_SIZE_PAQUETES_CRUDOS = 50 # Reducido para inserciones más frecuentes si es necesario
SUPPRESION_ALERTA_MINUTOS = 2
MAX_BUFFER_PAQUETES_CRUDOS = 10000 # Límite para evitar consumo excesivo de memoria

captura_activa = False # Inicia como detenida, Flask la activará

# Trackers para reglas stateful
syn_flood_tracker = defaultdict(lambda: {"count": 0, "first_seen": datetime.min, "ports": set()})
SYN_FLOOD_THRESHOLD = 20
SYN_FLOOD_WINDOW_SECONDS = 4

port_scan_tracker = defaultdict(lambda: {"ports": set(), "first_seen": datetime.min, "flags": defaultdict(int)})
PORT_SCAN_THRESHOLD_PORTS = 10
PORT_SCAN_WINDOW_SECONDS = 60

brute_force_tracker = defaultdict(lambda: deque(maxlen=10))
BRUTE_FORCE_THRESHOLD_ATTEMPTS = 4
BRUTE_FORCE_WINDOW_SECONDS = 120

IP_IDS = "0.0.0.0" # Se obtendrá dinámicamente

def inicializar_config_ids():
    global IP_IDS
    IP_IDS = obtener_ip_local()
    print(f"[ℹ️] IP del sistema IDS detectada: {IP_IDS}")
    print(f"[ℹ️] Supresión de alertas idénticas (IP origen, tipo, puerto_dst) por {SUPPRESION_ALERTA_MINUTOS} minutos.")

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except Exception:
        try:
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            if ip_local.startswith("127."):
                return socket.gethostbyname(socket.getfqdn()) # Intento más robusto
            return ip_local
        except Exception as e:
            print(f"[⚠️] Error crítico al obtener IP local: {e}. Usando 127.0.0.1.")
            return "127.0.0.1"

# ========================
# 🧠 REGISTRO DE EVENTOS DE SEGURIDAD
# ========================
def registrar_evento_seguridad(tipo, descripcion, ip_origen, nivel, detalles,
                               ip_destino=None, mac_origen=None, mac_destino=None,
                               so_origen=None, puerto_origen=None, puerto_destino=None, protocolo=None):
    ahora = datetime.now()
    clave_evento = (ip_origen, tipo, puerto_destino if puerto_destino else "N/A")

    with eventos_recientes_lock:
        if ahora - eventos_recientes_detalle[clave_evento] < timedelta(minutes=SUPPRESION_ALERTA_MINUTOS):
            return
        eventos_recientes_detalle[clave_evento] = ahora
    
    conn = conectar_db()
    if not conn:
        print(f"[⚠️] No se pudo registrar evento de seguridad (sin conexión a BD): {tipo} - {ip_origen}")
        return

    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO eventos_seguridad (
                tipo, descripcion, ip_origen, ip_destino, mac_origen, mac_destino,
                so_origen, puerto_origen, puerto_destino, protocolo,
                nivel, fecha, estado_alerta, estado_evento, detalles, repeticiones
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'nueva', 'activo', %s, 1)
        """
        valores = (
            tipo, descripcion, ip_origen, ip_destino, mac_origen, mac_destino,
            so_origen, int(puerto_origen) if puerto_origen is not None else None, 
            int(puerto_destino) if puerto_destino is not None else None, 
            protocolo, nivel, ahora, detalles
        )
        cursor.execute(sql, valores)
        print(f"[{nivel.upper()}] {tipo}: {descripcion} (Origen: {ip_origen}, Destino: {ip_destino or 'N/A'}, Puerto_Dst: {puerto_destino or 'N/A'})")
    except mariadb.Error as e:
        print(f"[⚠️] Error registrando evento de seguridad en BD: {e}")
    except Exception as ex:
        print(f"[⚠️] Error inesperado registrando evento de seguridad: {ex}")
    finally:
        if conn:
            conn.close()

# ========================
# 🔍 ANÁLISIS DE REGLAS
# ========================
def analizar_reglas(paquete):
    if not paquete.haslayer(IP):
        return

    ip_layer = paquete[IP]
    ip_origen = ip_layer.src
    ip_destino = ip_layer.dst
    ttl = ip_layer.ttl
    protocolo_num = ip_layer.proto
    
    puerto_origen, puerto_destino, flags_tcp, payload_str = None, None, "", ""

    if paquete.haslayer(TCP):
        tcp_layer = paquete[TCP]
        puerto_origen, puerto_destino, flags_tcp = tcp_layer.sport, tcp_layer.dport, tcp_layer.sprintf("%flags%")
        if tcp_layer.payload: payload_str = bytes(tcp_layer.payload).decode('utf-8', errors='ignore')
    elif paquete.haslayer(UDP):
        udp_layer = paquete[UDP]
        puerto_origen, puerto_destino = udp_layer.sport, udp_layer.dport
        if udp_layer.payload: payload_str = bytes(udp_layer.payload).decode('utf-8', errors='ignore')
    elif paquete.haslayer(ICMP) and paquete[ICMP].payload:
        payload_str = bytes(paquete[ICMP].payload).decode('utf-8', errors='ignore')

    mac_origen = paquete[Ether].src if paquete.haslayer(Ether) else "N/A"
    mac_destino = paquete[Ether].dst if paquete.haslayer(Ether) else "N/A"
    tamano_paquete = len(paquete)
    
    protocolos_ip = {1: "ICMP", 2: "IGMP", 6: "TCP", 17: "UDP", 47: "GRE", 50: "ESP", 51: "AH", 88: "EIGRP", 89: "OSPF"}
    nombre_protocolo_transporte = protocolos_ip.get(protocolo_num, f"Otro({protocolo_num})")

    so_origen = "Windows" if 100 <= ttl <= 128 else "Linux/Unix" if 60 <= ttl <= 64 else "Cisco/Solaris" if 250 <= ttl <= 255 else "Desconocido"
    
    payload_preview = payload_str[:150].replace('\n', ' ').replace('\r', '') + ('...' if len(payload_str) > 150 else '')
    detalles_completos = (
        f"IP_Dst: {ip_destino}, MAC_Src: {mac_origen}, MAC_Dst: {mac_destino}, "
        f"Port_Src: {puerto_origen or 'N/A'}, Port_Dst: {puerto_destino or 'N/A'}, "
        f"Proto: {nombre_protocolo_transporte}, TTL: {ttl}, Flags: {flags_tcp or 'N/A'}, "
        f"Size: {tamano_paquete}B, SO_Est: {so_origen}, Payload: '{payload_preview}'"
    )

    if ip_origen == IP_IDS and (ip_destino == IP_IDS or ip_destino.startswith("224.") or ip_destino == "255.255.255.255"):
        return

    ahora = datetime.now()

    # --- REGLAS DE DETECCIÓN ---
    # (Las reglas son las mismas que la versión anterior, solo se llama a registrar_evento_seguridad)

    # 1. SYN Flood
    if paquete.haslayer(TCP) and "S" in flags_tcp and not "A" in flags_tcp:
        tracker = syn_flood_tracker[(ip_origen, ip_destino, puerto_destino)]
        tracker["count"] += 1; tracker["ports"].add(puerto_origen)
        if tracker["count"] == 1: tracker["first_seen"] = ahora
        if (tracker["count"] >= SYN_FLOOD_THRESHOLD and (ahora - tracker["first_seen"]).total_seconds() <= SYN_FLOOD_WINDOW_SECONDS):
            desc = f"Posible SYN Flood: {tracker['count']} SYNs en {(ahora - tracker['first_seen']).total_seconds():.2f}s..."
            registrar_evento_seguridad("DoS - SYN Flood", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
            del syn_flood_tracker[(ip_origen, ip_destino, puerto_destino)]
        elif (ahora - tracker["first_seen"]).total_seconds() > SYN_FLOOD_WINDOW_SECONDS:
            del syn_flood_tracker[(ip_origen, ip_destino, puerto_destino)]

    # 2. Escaneo de Puertos
    if paquete.haslayer(TCP) and ip_destino != IP_IDS:
        scan_key = (ip_origen, ip_destino); tracker = port_scan_tracker[scan_key]
        if puerto_destino:
            tracker["ports"].add(puerto_destino)
            if "S" in flags_tcp and not "A" in flags_tcp: tracker["flags"]["SYN"] += 1
            elif "F" in flags_tcp and not ("A" in flags_tcp or "S" in flags_tcp or "R" in flags_tcp): tracker["flags"]["FIN"] += 1
            elif "F" in flags_tcp and "P" in flags_tcp and "U" in flags_tcp: tracker["flags"]["XMAS"] += 1
            elif not flags_tcp: tracker["flags"]["NULL"] += 1
            if tracker["first_seen"] == datetime.min: tracker["first_seen"] = ahora
            if len(tracker["ports"]) >= PORT_SCAN_THRESHOLD_PORTS and (ahora - tracker["first_seen"]).total_seconds() <= PORT_SCAN_WINDOW_SECONDS:
                scan_types = [stype for stype, count in tracker["flags"].items() if count > 0]
                scan_type_str = "/".join(scan_types) if scan_types else "Variado"
                desc = f"Escaneo de Puertos ({scan_type_str}): {ip_origen} escaneó {len(tracker['ports'])} puertos en {ip_destino}..."
                registrar_evento_seguridad(f"Reconocimiento - Escaneo {scan_type_str}", desc, ip_origen, "Medio" if "SYN" in scan_type_str else "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, None, None, nombre_protocolo_transporte)
                del port_scan_tracker[scan_key]
            elif (ahora - tracker["first_seen"]).total_seconds() > PORT_SCAN_WINDOW_SECONDS:
                del port_scan_tracker[scan_key]
    
    # 3. Acceso a Puertos Críticos
    puertos_servicios_comunes = { 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 443: "HTTPS", 3306: "MySQL/MariaDB", 3389: "RDP", 8080: "HTTP-Alt", 137:"NetBIOS-NS",138:"NetBIOS-DGM",139:"NetBIOS-SSN", 445:"SMB/CIFS" } # Expandida
    if puerto_destino in puertos_servicios_comunes and paquete.haslayer(TCP) and "S" in flags_tcp and not "A" in flags_tcp and not (ip_origen == IP_IDS and puerto_destino == 53):
        servicio = puertos_servicios_comunes[puerto_destino]
        desc = f"Intento de conexión SYN al servicio {servicio} (puerto {puerto_destino})."
        registrar_evento_seguridad(f"Acceso Servicio - {servicio}", desc, ip_origen, "Bajo", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 5. Protocolo IP No Común
    if protocolo_num not in protocolos_ip and protocolo_num != 41: # 41: IPv6 Encapsulation
        desc = f"Detectado uso de protocolo IP no estándar: {protocolo_num}."
        registrar_evento_seguridad("Red - Protocolo IP Inusual", desc, ip_origen, "Bajo", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, f"IP({protocolo_num})")

    # 6. ICMP Grande
    if nombre_protocolo_transporte == "ICMP" and tamano_paquete > 1024:
        desc = f"Paquete ICMP grande ({tamano_paquete} bytes). Posible Ping of Death."
        registrar_evento_seguridad("DoS - ICMP Grande", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 7. Fragmentación IP
    if ip_layer.flags.MF or ip_layer.frag > 0:
        desc = f"Paquete IP fragmentado (flags: {ip_layer.flags}, offset: {ip_layer.frag}). Posible evasión."
        registrar_evento_seguridad("Evasión - Fragmentación IP", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 8. Payload Sospechoso
    patrones_payload_criticos = {"rm -rf /": "Eliminación raíz", "etc/shadow": "Acceso a contraseñas", "powershell -enc": "PS Codificado", "cmd.exe /c": "CMD", "union select": "SQLi", "<script>alert": "XSS", "meterpreter": "Metasploit"}
    if payload_str:
        payload_lower = payload_str.lower()
        for patron, desc_patron in patrones_payload_criticos.items():
            if patron in payload_lower:
                desc = f"Patrón '{patron}' ({desc_patron}) detectado en payload."
                registrar_evento_seguridad("Amenaza - Payload Sospechoso", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
                break
    
    # 9. Puertos C&C
    puertos_cnc_sospechosos = [6667, 4444, 5555, 1337]
    if puerto_destino in puertos_cnc_sospechosos and ip_origen != IP_IDS:
        desc = f"Conexión saliente a puerto {puerto_destino} (potencial C&C)."
        registrar_evento_seguridad("Amenaza - Posible C&C", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 10. Fuerza Bruta
    servicios_fuerza_bruta = {21: "FTP", 22: "SSH", 3389: "RDP"}
    if puerto_destino in servicios_fuerza_bruta and paquete.haslayer(TCP) and "S" in flags_tcp and not "A" in flags_tcp:
        tracker_key = (ip_origen, ip_destino, puerto_destino); tracker = brute_force_tracker[tracker_key]; tracker.append(ahora)
        intentos_recientes = [t for t in tracker if (ahora - t).total_seconds() <= BRUTE_FORCE_WINDOW_SECONDS]
        if len(intentos_recientes) >= BRUTE_FORCE_THRESHOLD_ATTEMPTS:
            servicio = servicios_fuerza_bruta[puerto_destino]
            desc = f"Posible Fuerza Bruta a {servicio}: {len(intentos_recientes)} SYNs en {BRUTE_FORCE_WINDOW_SECONDS}s."
            registrar_evento_seguridad(f"Ataque - Fuerza Bruta {servicio}", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
            brute_force_tracker[tracker_key].clear()
        while tracker and (ahora - tracker[0]).total_seconds() > BRUTE_FORCE_WINDOW_SECONDS: tracker.popleft()

    # 11. DNS Anómalo (Grande)
    if nombre_protocolo_transporte == "UDP" and puerto_destino == 53 and tamano_paquete > 512:
        desc = f"Paquete DNS ({nombre_protocolo_transporte}) grande ({tamano_paquete} bytes). Posible túnel."
        registrar_evento_seguridad("Red - DNS Anómalo (Grande)", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 12. User-Agent Sospechoso (HTTP)
    if nombre_protocolo_transporte == "TCP" and puerto_destino == 80 and payload_str:
        payload_lower = payload_str.lower()
        if "user-agent:" in payload_lower:
            ua_start = payload_lower.find("user-agent:") + len("user-agent:")
            ua_end = payload_lower.find("\r\n", ua_start)
            user_agent = payload_str[ua_start:ua_end].strip() if ua_end != -1 else payload_str[ua_start:].strip()
            uas_sospechosas = ["nmap", "sqlmap", "nikto", "curl/", "wget/", "<script>", "() { :;};"]
            if any(susp_ua in user_agent.lower() for susp_ua in uas_sospechosas):
                desc = f"User-Agent HTTP sospechoso: '{user_agent[:50]}...'." # Acortar UA en descripción
                registrar_evento_seguridad("Web - User-Agent Sospechoso", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)


# ========================
# 📡 PROCESAR PAQUETE (Wrapper y Llenado de Buffer para Paquetes Crudos)
# ========================
def procesar_paquete_wrapper(paquete):
    try:
        analizar_reglas(paquete) # Análisis para eventos de seguridad

        # Llenar buffer para la tabla 'escanear_red' (paquetes crudos)
        if paquete.haslayer(IP):
            ip_layer = paquete[IP]
            proto_num = ip_layer.proto
            protocolos_ip = {1: "ICMP", 6: "TCP", 17: "UDP"} # Simplificado para tabla cruda
            nombre_proto = protocolos_ip.get(proto_num, f"Otro({proto_num})")
            
            # Extraer solo los campos necesarios para 'escanear_red'
            # Asegúrate que estos campos coincidan con tu tabla 'escanear_red'
            info_paquete_crudo = (
                ip_layer.src,
                ip_layer.dst,
                paquete[Ether].src if paquete.haslayer(Ether) else None,
                paquete[Ether].dst if paquete.haslayer(Ether) else None,
                paquete.sport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None,
                paquete.dport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None,
                nombre_proto, # Nombre del protocolo de transporte
                len(paquete), # Tamaño total del paquete
                ip_layer.ttl,
                paquete.sprintf("%TCP.flags%") if paquete.haslayer(TCP) else None,
                str(bytes(paquete.payload)[:50]), # Preview del payload de la capa IP
                datetime.now() # Fecha de captura
            )
            with buffer_lock:
                if len(paquetes_buffer_crudos) < MAX_BUFFER_PAQUETES_CRUDOS:
                    paquetes_buffer_crudos.append(info_paquete_crudo)
                else:
                    print(f"[⚠️] Buffer de paquetes crudos lleno ({MAX_BUFFER_PAQUETES_CRUDOS}). Descartando.")


    except Exception as e:
        print(f"[⚠️] Error crítico procesando paquete: {e} - Paquete: {paquete.summary() if paquete else 'N/A'}")

# ========================
# 💾 INSERCIÓN DE PAQUETES CRUDOS EN LOTES
# ========================
def insertar_paquetes_crudos_en_lote():
    global paquetes_buffer_crudos
    while True: # Este hilo correrá mientras 'captura_activa' sea True en el contexto de Flask
        time.sleep(1) # Intervalo para insertar en BD, puede ser más largo
        
        if not captura_activa and not paquetes_buffer_crudos: # Si la captura se detuvo y el buffer está vacío
            break # Terminar el hilo si no hay nada que hacer y la captura está detenida

        lote_actual = []
        with buffer_lock:
            if paquetes_buffer_crudos:
                lote_actual = list(paquetes_buffer_crudos)
                paquetes_buffer_crudos.clear()

        if not lote_actual:
            continue

        conn = conectar_db()
        if not conn:
            print(f"[⚠️] No se pudieron insertar {len(lote_actual)} paquetes crudos (sin conexión a BD). Re-encolando...")
            with buffer_lock: # Devolver al buffer si falla la conexión (cuidado con bucles infinitos si la BD nunca vuelve)
                paquetes_buffer_crudos = lote_actual + paquetes_buffer_crudos 
            continue
        
        try:
            cursor = conn.cursor()
            # Asegúrate que el orden y número de %s coincida con tu tabla 'escanear_red'
            # y con los datos en 'info_paquete_crudo'
            sql_insert = """
                INSERT INTO escanear_red (
                    iporigen, ipdestino, mac_origen, mac_destino, 
                    puerto_origen, puerto_destino, protocolo_nombre, tamano, ttl, 
                    flags_tcp, payload, fecha_captura 
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Los datos en lote_actual ya deben tener el formato correcto (12 campos)
            cursor.executemany(sql_insert, lote_actual)
            # print(f"[💾] {len(lote_actual)} paquetes crudos insertados en 'escanear_red'.")
        except mariadb.Error as e:
            print(f"[⚠️] Error al insertar paquetes crudos en 'escanear_red': {e}")
            # Considerar re-encolar los paquetes si la inserción falla por razones transitorias
            # with buffer_lock: paquetes_buffer_crudos = lote_actual + paquetes_buffer_crudos
        except Exception as ex_general:
            print(f"[⚠️] Error general insertando paquetes crudos: {ex_general}")
        finally:
            if conn:
                conn.close()
    print("[ℹ️] Hilo de inserción de paquetes crudos finalizado.")


# ========================
# ▶️ FUNCIONES DE CONTROL DE CAPTURA (Para ser llamadas por Flask)
# ========================
sniffer_thread = None
inserter_thread = None # Hilo para insertar paquetes crudos

def iniciar_proceso_captura():
    global captura_activa, sniffer_thread, inserter_thread
    if captura_activa:
        print("[ℹ️] La captura ya está activa.")
        return False

    inicializar_config_ids() # Obtener IP_IDS etc.
    
    # Verificar conexión a BD antes de iniciar
    test_conn = conectar_db()
    if not test_conn:
        print("[❌] No se puede iniciar captura: Fallo en la conexión a la base de datos.")
        return False
    test_conn.close()
    print("[✅] Conexión a BD verificada para iniciar captura.")

    captura_activa = True
    
    # Iniciar el sniffer en un hilo
    sniffer_thread = threading.Thread(target=lambda: sniff(prn=procesar_paquete_wrapper, store=False, stop_filter=lambda x: not captura_activa), daemon=True)
    sniffer_thread.start()
    print("[📡] Hilo de captura de paquetes iniciado.")

    # Iniciar el hilo para insertar paquetes crudos, si se desea esta funcionalidad
    if not inserter_thread or not inserter_thread.is_alive():
        paquetes_buffer_crudos.clear() # Limpiar buffer por si acaso
        inserter_thread = threading.Thread(target=insertar_paquetes_crudos_en_lote, daemon=True)
        inserter_thread.start()
        print("[✍️] Hilo de inserción de paquetes crudos iniciado.")
    
    print(f"[🚀] IDS {socket.gethostname()} ({IP_IDS}) captura iniciada.")
    return True

def detener_proceso_captura():
    global captura_activa
    if not captura_activa:
        print("[ℹ️] La captura ya está detenida.")
        return False
    
    print("[🛑] Solicitud para detener IDS...")
    captura_activa = False # Esto detendrá el bucle de sniff y el de inserción
    
    # Esperar a que los hilos terminen (opcional, pero bueno para limpieza)
    if sniffer_thread and sniffer_thread.is_alive():
        print("[⏳] Esperando finalización del hilo de captura...")
        sniffer_thread.join(timeout=5) # Esperar máximo 5 segundos
        if sniffer_thread.is_alive():
            print("[⚠️] El hilo de captura no finalizó a tiempo.")
    
    if inserter_thread and inserter_thread.is_alive():
        print("[⏳] Esperando finalización del hilo de inserción de paquetes crudos...")
        inserter_thread.join(timeout=12) # Darle un poco más de tiempo para vaciar buffer
        if inserter_thread.is_alive():
            print("[⚠️] El hilo de inserción de paquetes crudos no finalizó a tiempo.")

    print("[👋] IDS detenido completamente.")
    return True

# ========================
# 🚦 PUNTO DE ENTRADA (Si se ejecuta directamente)
# ========================
if __name__ == "__main__":
    if iniciar_proceso_captura():
        print("[⌨️] IDS en ejecución directa. Presiona Ctrl+C para detener.")
        try:
            while captura_activa:
                time.sleep(1)
        except KeyboardInterrupt:
            detener_proceso_captura()
    else:
        print("[💥] No se pudo iniciar el IDS directamente.")


