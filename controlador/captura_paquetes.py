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
            autocommit=False # Cambiado a False para manejo explícito de transacciones
        )
        return conn
    except mariadb.Error as e:
        print(f"[❌] Error conectando a MariaDB: {e}.")
        return None

# ========================
# ⚙️ VARIABLES GLOBALES Y CONFIGURACIÓN
# ========================
buffer_lock = threading.Lock()
paquetes_buffer_crudos = [] 

VENTANA_AGREGACION_ALERTAS_MINUTOS = 60 
MAX_BUFFER_PAQUETES_CRUDOS = 10000
BATCH_SIZE_PAQUETES_CRUDOS = 50

captura_activa = False

syn_flood_tracker = defaultdict(lambda: {"count": 0, "first_seen": datetime.min, "ports": set()})
SYN_FLOOD_THRESHOLD = 20
SYN_FLOOD_WINDOW_SECONDS = 4

port_scan_tracker = defaultdict(lambda: {"ports": set(), "first_seen": datetime.min, "flags": defaultdict(int)})
PORT_SCAN_THRESHOLD_PORTS = 10
PORT_SCAN_WINDOW_SECONDS = 60

brute_force_tracker = defaultdict(lambda: deque(maxlen=10)) 
BRUTE_FORCE_THRESHOLD_ATTEMPTS = 4 
BRUTE_FORCE_WINDOW_SECONDS = 120 

IP_IDS = "0.0.0.0"

def inicializar_config_ids():
    global IP_IDS
    IP_IDS = obtener_ip_local()
    print(f"[ℹ️] IP del sistema IDS detectada: {IP_IDS}")
    print(f"[ℹ️] Agregación de alertas idénticas (IP origen, tipo, IP destino, puerto_dst) si ocurren dentro de {VENTANA_AGREGACION_ALERTAS_MINUTOS} minutos.")

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
                interfaces = socket.getaddrinfo(hostname, None)
                for interface in interfaces:
                    if interface[0] == socket.AF_INET and not interface[4][0].startswith("127."):
                        return interface[4][0]
                return socket.gethostbyname(socket.getfqdn()) 
            return ip_local
        except Exception as e:
            print(f"[⚠️] Error crítico al obtener IP local: {e}. Usando 127.0.0.1.")
            return "127.0.0.1"

# ========================
# 🧠 REGISTRO DE EVENTOS DE SEGURIDAD (CON AGREGACIÓN Y CORRECCIÓN DE NOMBRE DE COLUMNA)
# ========================
def registrar_evento_seguridad(tipo, descripcion, ip_origen, nivel, detalles,
                               ip_destino=None, mac_origen=None, mac_destino=None,
                               so_origen=None, puerto_origen=None, puerto_destino=None, protocolo=None):
    ahora = datetime.now()
    conn = conectar_db()
    if not conn:
        print(f"[⚠️] No se pudo registrar evento de seguridad (sin conexión a BD): {tipo} - {descripcion} (Origen: {ip_origen})")
        return

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True) 

        tiempo_agregacion_limite = ahora - timedelta(minutes=VENTANA_AGREGACION_ALERTAS_MINUTOS)

        # ***** CORRECCIÓN AQUÍ: Cambiado 'id_evento_seguridad' a 'id_evento' *****
        sql_find_existing = """
            SELECT id_evento, repeticiones, nivel as nivel_existente, descripcion as desc_existente 
            FROM eventos_seguridad
            WHERE ip_origen = %s AND tipo = %s 
              AND COALESCE(puerto_destino, -1) = COALESCE(%s, -1)
              AND COALESCE(ip_destino, '0.0.0.0') = COALESCE(%s, '0.0.0.0')
              AND estado_alerta IN ('nueva', 'activa') 
              AND fecha > %s 
            ORDER BY fecha DESC LIMIT 1
        """
        cursor.execute(sql_find_existing, (
            ip_origen, tipo, 
            puerto_destino, ip_destino, 
            tiempo_agregacion_limite
        ))
        evento_existente = cursor.fetchone()

        if evento_existente:
            # ***** CORRECCIÓN AQUÍ: Cambiado 'id_evento_seguridad' a 'id_evento' *****
            id_existente = evento_existente['id_evento'] 
            nuevas_repeticiones = evento_existente['repeticiones'] + 1
            
            niveles_orden = {"Bajo": 1, "Medio": 2, "Alto": 3}
            nivel_actualizar = nivel
            if niveles_orden.get(evento_existente['nivel_existente'], 0) > niveles_orden.get(nivel, 0):
                nivel_actualizar = evento_existente['nivel_existente']

            descripcion_actualizar = descripcion 

            # ***** CORRECCIÓN AQUÍ: Cambiado 'id_evento_seguridad' a 'id_evento' *****
            sql_update = """
                UPDATE eventos_seguridad 
                SET fecha = %s, repeticiones = %s, detalles = %s, nivel = %s, descripcion = %s
                WHERE id_evento = %s
            """
            cursor.execute(sql_update, (ahora, nuevas_repeticiones, detalles, nivel_actualizar, descripcion_actualizar, id_existente))
            conn.commit()
            print(f"[{nivel_actualizar.upper()}] EVENTO ACTUALIZADO (x{nuevas_repeticiones}): {tipo} - {descripcion_actualizar} (Origen: {ip_origen}, IP_Dst: {ip_destino or 'N/A'}, Puerto_Dst: {puerto_destino or 'N/A'})")
        else:
            sql_insert = """
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
            cursor.execute(sql_insert, valores)
            conn.commit()
            print(f"[{nivel.upper()}] NUEVO EVENTO: {tipo} - {descripcion} (Origen: {ip_origen}, IP_Dst: {ip_destino or 'N/A'}, Puerto_Dst: {puerto_destino or 'N/A'})")

    except mariadb.Error as e:
        print(f"[⚠️] Error de BD registrando evento de seguridad: {e}")
        if conn: conn.rollback()
    except Exception as ex:
        print(f"[⚠️] Error inesperado registrando evento de seguridad: {ex}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ========================
# 🔍 ANÁLISIS DE REGLAS (CON DESCRIPCIONES MEJORADAS)
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
        if tcp_layer.payload: payload_str = bytes(tcp_layer.payload).decode('utf-8', errors='replace') 
    elif paquete.haslayer(UDP):
        udp_layer = paquete[UDP]
        puerto_origen, puerto_destino = udp_layer.sport, udp_layer.dport
        if udp_layer.payload: payload_str = bytes(udp_layer.payload).decode('utf-8', errors='replace') 
    elif paquete.haslayer(ICMP) and paquete[ICMP].payload:
        payload_str = bytes(paquete[ICMP].payload).decode('utf-8', errors='replace') 

    mac_origen = paquete[Ether].src if paquete.haslayer(Ether) else "N/A"
    mac_destino = paquete[Ether].dst if paquete.haslayer(Ether) else "N/A"
    tamano_paquete = len(paquete)
    
    protocolos_ip = {1: "ICMP", 2: "IGMP", 6: "TCP", 17: "UDP", 47: "GRE", 50: "ESP", 51: "AH", 88: "EIGRP", 89: "OSPF"}
    nombre_protocolo_transporte = protocolos_ip.get(protocolo_num, f"Otro({protocolo_num})")

    so_origen = "Windows" if 100 <= ttl <= 128 else "Linux/Unix" if 60 <= ttl <= 64 else "Cisco/Solaris" if 250 <= ttl <= 255 else "Desconocido (TTL irregular)"
    
    payload_preview = payload_str[:150].replace('\n', ' ').replace('\r', '') + ('...' if len(payload_str) > 150 else '')
    detalles_completos = (
        f"IP_Dst: {ip_destino}, MAC_Src: {mac_origen}, MAC_Dst: {mac_destino}, "
        f"Port_Src: {puerto_origen or 'N/A'}, Port_Dst: {puerto_destino or 'N/A'}, "
        f"Proto_Transporte: {nombre_protocolo_transporte}, Proto_IP_Num: {protocolo_num}, TTL: {ttl}, Flags_TCP: {flags_tcp or 'N/A'}, "
        f"PacketSize: {tamano_paquete}B, SO_Estimado: {so_origen}, PayloadPreview: '{payload_preview}'"
    )

    if ip_origen == IP_IDS and (ip_destino == IP_IDS or ip_destino.startswith("224.") or ip_destino == "255.255.255.255"):
        return 

    ahora = datetime.now()

    # --- REGLAS DE DETECCIÓN ---

    # 1. SYN Flood
    if paquete.haslayer(TCP) and "S" in flags_tcp and not "A" in flags_tcp: 
        tracker = syn_flood_tracker[(ip_origen, ip_destino, puerto_destino)]
        tracker["count"] += 1
        tracker["ports"].add(puerto_origen) 
        if tracker["count"] == 1: tracker["first_seen"] = ahora
        
        elapsed_seconds = (ahora - tracker["first_seen"]).total_seconds()
        if tracker["count"] >= SYN_FLOOD_THRESHOLD and elapsed_seconds <= SYN_FLOOD_WINDOW_SECONDS:
            desc = (f"Detectado posible ataque de inundación SYN desde {ip_origen} hacia {ip_destino}:{puerto_destino}. "
                    f"Se observaron {tracker['count']} paquetes SYN sin ACK en {elapsed_seconds:.2f}s (umbral: {SYN_FLOOD_THRESHOLD} en {SYN_FLOOD_WINDOW_SECONDS}s). "
                    f"Esto puede agotar los recursos del servidor destino.")
            registrar_evento_seguridad("DoS - SYN Flood", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
            del syn_flood_tracker[(ip_origen, ip_destino, puerto_destino)] 
        elif elapsed_seconds > SYN_FLOOD_WINDOW_SECONDS: 
            del syn_flood_tracker[(ip_origen, ip_destino, puerto_destino)]

    # 2. Escaneo de Puertos
    if paquete.haslayer(TCP) and ip_destino != IP_IDS: 
        scan_key = (ip_origen, ip_destino)
        tracker = port_scan_tracker[scan_key]
        if puerto_destino: 
            tracker["ports"].add(puerto_destino)
            if "S" in flags_tcp and not "A" in flags_tcp: tracker["flags"]["SYN"] += 1
            elif "F" in flags_tcp and not ("A" in flags_tcp or "S" in flags_tcp or "R" in flags_tcp): tracker["flags"]["FIN"] += 1
            elif "F" in flags_tcp and "P" in flags_tcp and "U" in flags_tcp: tracker["flags"]["XMAS"] += 1
            elif not flags_tcp: tracker["flags"]["NULL"] += 1
            
            if not tracker["first_seen"] or tracker["first_seen"] == datetime.min: tracker["first_seen"] = ahora
            
            elapsed_seconds = (ahora - tracker["first_seen"]).total_seconds()
            if len(tracker["ports"]) >= PORT_SCAN_THRESHOLD_PORTS and elapsed_seconds <= PORT_SCAN_WINDOW_SECONDS:
                scan_types = [stype for stype, count in tracker["flags"].items() if count > 0]
                scan_type_str = "/".join(scan_types) if scan_types else "Variado"
                nivel_scan = "Alto" if scan_type_str not in ["SYN", "Variado"] else "Medio" 
                desc = (f"Detectado escaneo de puertos tipo '{scan_type_str}' desde {ip_origen}. "
                        f"Se accedieron {len(tracker['ports'])} puertos distintos en {ip_destino} en {elapsed_seconds:.2f}s (umbral: {PORT_SCAN_THRESHOLD_PORTS} puertos en {PORT_SCAN_WINDOW_SECONDS}s). "
                        f"Esto indica una fase de reconocimiento de servicios.")
                registrar_evento_seguridad(f"Reconocimiento - Escaneo {scan_type_str}", desc, ip_origen, nivel_scan, detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, None, None, "TCP")
                del port_scan_tracker[scan_key]
            elif elapsed_seconds > PORT_SCAN_WINDOW_SECONDS:
                del port_scan_tracker[scan_key]
    
    # 3. Acceso a Puertos Críticos/Servicios Comunes
    puertos_servicios_comunes = { 
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS Query", 80: "HTTP", 137:"NetBIOS-NS",
        138:"NetBIOS-DGM",139:"NetBIOS-SSN", 443: "HTTPS", 445:"SMB/CIFS", 
        3306: "MySQL/MariaDB", 3389: "RDP", 5900: "VNC", 8080: "HTTP-Alt"
    }
    if puerto_destino in puertos_servicios_comunes and paquete.haslayer(TCP) and "S" in flags_tcp and not "A" in flags_tcp:
        if ip_origen == IP_IDS and puerto_destino == 53:
            pass 
        else:
            servicio = puertos_servicios_comunes[puerto_destino]
            desc = (f"Intento de conexión inicial (SYN) detectado desde {ip_origen}:{puerto_origen} al servicio '{servicio}' en {ip_destino}:{puerto_destino}. "
                    f"Esto podría ser un intento de acceso o una etapa de reconocimiento.")
            registrar_evento_seguridad(f"Acceso Servicio - {servicio}", desc, ip_origen, "Bajo", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 5. Protocolo IP No Común
    protocolos_ip_conocidos_nums = list(protocolos_ip.keys()) + [41] 
    if protocolo_num not in protocolos_ip_conocidos_nums:
        desc = (f"Detectado uso de protocolo IP no estándar o poco común (Número: {protocolo_num}) en tráfico desde {ip_origen} hacia {ip_destino}. "
                f"Esto podría indicar un intento de evasión o tráfico especializado.")
        registrar_evento_seguridad("Red - Protocolo IP Inusual", desc, ip_origen, "Bajo", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, f"IP({protocolo_num})")

    # 6. ICMP Grande
    if nombre_protocolo_transporte == "ICMP" and tamano_paquete > 1024: 
        tipo_icmp = paquete[ICMP].type
        desc = (f"Detectado paquete ICMP inusualmente grande ({tamano_paquete} bytes, tipo {tipo_icmp}) desde {ip_origen} hacia {ip_destino}. "
                f"Esto podría ser un intento de ataque 'Ping of Death' o una configuración de red anómala.")
        registrar_evento_seguridad("DoS - ICMP Grande", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 7. Fragmentación IP
    if ip_layer.flags.MF or ip_layer.frag > 0: 
        desc = (f"Detectado paquete IP fragmentado desde {ip_origen} hacia {ip_destino} (flags: {ip_layer.flags}, offset: {ip_layer.frag}). "
                f"La fragmentación excesiva o maliciosa puede ser usada para evadir sistemas de detección o causar DoS.")
        registrar_evento_seguridad("Evasión - Fragmentación IP", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 8. Payload Sospechoso
    patrones_payload_criticos = {
        "rm -rf /": "Comando de eliminación raíz (Linux/Unix)", 
        "etc/shadow": "Intento de acceso a archivo de contraseñas (Linux/Unix)",
        "powershell -enc": "Ejecución de PowerShell codificado (Windows)", 
        "cmd.exe /c": "Ejecución de Command Prompt (Windows)",
        "union select": "Técnica común de Inyección SQL", 
        "<script>alert": "Patrón básico de Cross-Site Scripting (XSS)", 
        "meterpreter": "Payload de Metasploit (Herramienta de Hacking)",
        "netcat": "Uso de Netcat (Herramienta de red versátil)",
        "nc -e": "Uso de Netcat con ejecución de comando"
    }
    if payload_str: 
        payload_lower_para_busqueda = payload_str.lower() 
        for patron, desc_patron in patrones_payload_criticos.items():
            if patron.lower() in payload_lower_para_busqueda:
                desc = (f"Detectado patrón de payload sospechoso '{patron}' (asociado con '{desc_patron}') en tráfico desde {ip_origen} hacia {ip_destino} (puerto {puerto_destino or 'N/A'}). "
                        f"Esto podría indicar un intento de explotación, ejecución remota de comandos, o la presencia de malware.")
                registrar_evento_seguridad("Amenaza - Payload Sospechoso", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
                break 

    # 9. Puertos Comunes de C&C
    puertos_cnc_sospechosos = [6667, 4444, 5555, 1337, 8443, 31337] 
    if puerto_destino in puertos_cnc_sospechosos and ip_origen != IP_IDS: 
        desc = (f"Detectada conexión saliente desde {ip_origen} hacia {ip_destino} en el puerto {puerto_destino}. "
                f"Este puerto es comúnmente utilizado para comunicación de Comando y Control (C&C) por malware.")
        registrar_evento_seguridad("Amenaza - Posible C&C", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 10. Fuerza Bruta
    servicios_fuerza_bruta = {21: "FTP", 22: "SSH", 3389: "RDP", 25: "SMTP-AUTH (proxy)", 110: "POP3 (proxy)", 143: "IMAP (proxy)", 3306: "MySQL/MariaDB (proxy)"} 
    if puerto_destino in servicios_fuerza_bruta and paquete.haslayer(TCP) and "S" in flags_tcp and not "A" in flags_tcp:
        tracker_key = (ip_origen, ip_destino, puerto_destino)
        tracker = brute_force_tracker[tracker_key]
        tracker.append(ahora)
        
        intentos_validos_en_ventana = [t for t in tracker if (ahora - t).total_seconds() <= BRUTE_FORCE_WINDOW_SECONDS]
        
        if len(intentos_validos_en_ventana) >= BRUTE_FORCE_THRESHOLD_ATTEMPTS:
            servicio = servicios_fuerza_bruta[puerto_destino]
            desc = (f"Detectada posible actividad de fuerza bruta hacia el servicio '{servicio}' en {ip_destino}:{puerto_destino} desde {ip_origen}. "
                    f"Se observaron {len(intentos_validos_en_ventana)} intentos de conexión (SYN) en los últimos {BRUTE_FORCE_WINDOW_SECONDS} segundos (umbral: {BRUTE_FORCE_THRESHOLD_ATTEMPTS}).")
            registrar_evento_seguridad(f"Ataque - Fuerza Bruta {servicio}", desc, ip_origen, "Alto", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
            brute_force_tracker[tracker_key].clear() 
        
        while tracker and (ahora - tracker[0]).total_seconds() > BRUTE_FORCE_WINDOW_SECONDS:
            tracker.popleft()

    # 11. DNS Anómalo
    if nombre_protocolo_transporte == "UDP" and puerto_destino == 53 and tamano_paquete > 512: 
        desc = (f"Detectado paquete DNS sobre UDP inusualmente grande ({tamano_paquete} bytes) desde {ip_origen} hacia {ip_destino}:{puerto_destino}. "
                f"Esto podría indicar uso de EDNS, una respuesta grande legítima, o un posible intento de túnel de datos vía DNS o DoS (amplificación).")
        registrar_evento_seguridad("Red - DNS Anómalo (Grande)", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)

    # 12. User-Agent Sospechoso
    if nombre_protocolo_transporte == "TCP" and puerto_destino == 80 and payload_str:
        payload_lower_para_ua = payload_str.lower()
        ua_header_key = "user-agent:"
        if ua_header_key in payload_lower_para_ua:
            try:
                ua_start_index = payload_lower_para_ua.find(ua_header_key) + len(ua_header_key)
                ua_end_index = payload_lower_para_ua.find("\r\n", ua_start_index)
                user_agent_raw = payload_str[ua_start_index : (ua_end_index if ua_end_index != -1 else len(payload_str))].strip()
                
                uas_sospechosas = ["nmap", "sqlmap", "nikto", "curl/", "wget/", "<script>", "() { :;};", "masscan", "dirb", "gobuster"] 
                user_agent_lower = user_agent_raw.lower()
                for susp_ua_pattern in uas_sospechosas:
                    if susp_ua_pattern in user_agent_lower:
                        desc = (f"Detectado User-Agent HTTP sospechoso o asociado a herramientas de escaneo/hacking en tráfico desde {ip_origen} hacia {ip_destino}. "
                                f"User-Agent: '{user_agent_raw[:70]}{'...' if len(user_agent_raw)>70 else ''}'. Patrón detectado: '{susp_ua_pattern}'.")
                        registrar_evento_seguridad("Web - User-Agent Sospechoso", desc, ip_origen, "Medio", detalles_completos, ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo_transporte)
                        break 
            except Exception as e_ua:
                print(f"[⚠️] Error parseando User-Agent: {e_ua}")


# ========================
# 📡 PROCESAR PAQUETE (Wrapper y Llenado de Buffer para Paquetes Crudos)
# ========================
def procesar_paquete_wrapper(paquete):
    try:
        analizar_reglas(paquete) 

        if paquete.haslayer(IP):
            ip_layer = paquete[IP]
            proto_num = ip_layer.proto
            protocolos_ip_simples = {1: "ICMP", 6: "TCP", 17: "UDP"} 
            nombre_proto = protocolos_ip_simples.get(proto_num, f"Otro({proto_num})")
            
            payload_preview_crudo = ""
            if paquete.haslayer(TCP) and paquete[TCP].payload:
                payload_preview_crudo = str(bytes(paquete[TCP].payload)[:50])
            elif paquete.haslayer(UDP) and paquete[UDP].payload:
                payload_preview_crudo = str(bytes(paquete[UDP].payload)[:50])
            elif paquete.haslayer(ICMP) and paquete[ICMP].payload:
                 payload_preview_crudo = str(bytes(paquete[ICMP].payload)[:50])
            elif ip_layer.payload: 
                 payload_preview_crudo = str(bytes(ip_layer.payload)[:50])

            info_paquete_crudo = (
                ip_layer.src,
                ip_layer.dst,
                paquete[Ether].src if paquete.haslayer(Ether) else None,
                paquete[Ether].dst if paquete.haslayer(Ether) else None,
                paquete.sport if hasattr(paquete, 'sport') else None,
                paquete.dport if hasattr(paquete, 'dport') else None,
                nombre_proto, 
                len(paquete), 
                ip_layer.ttl,
                paquete.sprintf("%TCP.flags%") if paquete.haslayer(TCP) else None,
                payload_preview_crudo, 
                datetime.now() 
            )
            with buffer_lock:
                if len(paquetes_buffer_crudos) < MAX_BUFFER_PAQUETES_CRUDOS:
                    paquetes_buffer_crudos.append(info_paquete_crudo)
                else:
                    pass 

    except Exception as e:
        print(f"[⚠️] Error crítico procesando paquete: {e} - Paquete: {paquete.summary() if paquete else 'N/A'}")

# ========================
# 💾 INSERCIÓN DE PAQUETES CRUDOS EN LOTES
# ========================
def insertar_paquetes_crudos_en_lote():
    global paquetes_buffer_crudos
    print("[ℹ️] Iniciando hilo de inserción de paquetes crudos en BD...")
    while captura_activa or paquetes_buffer_crudos: 
        
        lote_actual = []
        if paquetes_buffer_crudos: 
            with buffer_lock:
                if paquetes_buffer_crudos: 
                    num_a_tomar = min(len(paquetes_buffer_crudos), BATCH_SIZE_PAQUETES_CRUDOS)
                    lote_actual = paquetes_buffer_crudos[:num_a_tomar]
                    paquetes_buffer_crudos = paquetes_buffer_crudos[num_a_tomar:]

        if not lote_actual:
            time.sleep(0.5) 
            if not captura_activa and not paquetes_buffer_crudos: 
                break
            continue

        conn = conectar_db()
        if not conn:
            print(f"[⚠️] DB Inserción Crudos: No se pudieron insertar {len(lote_actual)} paq. (sin conexión). Re-encolando...")
            with buffer_lock: 
                paquetes_buffer_crudos = lote_actual + paquetes_buffer_crudos 
            time.sleep(5) 
            continue
        
        cursor = None
        try:
            cursor = conn.cursor()
            sql_insert = """
                INSERT INTO escanear_red (
                    iporigen, ipdestino, mac_origen, mac_destino, 
                    puerto_origen, puerto_destino, protocolo_nombre, tamano, ttl, 
                    flags_tcp, payload, fecha_captura 
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql_insert, lote_actual)
            conn.commit() 
        except mariadb.Error as e:
            print(f"[⚠️] DB Inserción Crudos: Error MariaDB: {e}. Re-encolando {len(lote_actual)} paquetes.")
            if conn: conn.rollback()
            with buffer_lock: paquetes_buffer_crudos = lote_actual + paquetes_buffer_crudos
        except Exception as ex_general: 
            print(f"[⚠️] DB Inserción Crudos: Error General: {ex_general}. Re-encolando {len(lote_actual)} paquetes.")
            if conn: conn.rollback() 
            with buffer_lock: paquetes_buffer_crudos = lote_actual + paquetes_buffer_crudos
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
        time.sleep(0.1) 

    print("[ℹ️] Hilo de inserción de paquetes crudos finalizado.")


# ========================
# ▶️ FUNCIONES DE CONTROL DE CAPTURA (Para ser llamadas por Flask)
# ========================
sniffer_thread = None
inserter_thread = None 

def iniciar_proceso_captura():
    global captura_activa, sniffer_thread, inserter_thread
    if captura_activa:
        print("[ℹ️] La captura ya está activa.")
        return False

    inicializar_config_ids() 
    
    test_conn = conectar_db()
    if not test_conn:
        print("[❌] No se puede iniciar captura: Fallo en la conexión a la base de datos.")
        return False
    test_conn.close()
    print("[✅] Conexión a BD verificada para iniciar captura.")

    captura_activa = True
    
    sniffer_thread = threading.Thread(target=lambda: sniff(prn=procesar_paquete_wrapper, store=False, stop_filter=lambda x: not captura_activa, filter="ip or arp or rarp"), daemon=True)
    sniffer_thread.start()
    print("[📡] Hilo de captura de paquetes iniciado (filtro: 'ip or arp or rarp').")

    if not inserter_thread or not inserter_thread.is_alive():
        with buffer_lock: 
            paquetes_buffer_crudos.clear() 
        inserter_thread = threading.Thread(target=insertar_paquetes_crudos_en_lote, daemon=True)
        inserter_thread.start()
        print("[✍️] Hilo de inserción de paquetes crudos iniciado.")
    
    print(f"[🚀] IDS en {socket.gethostname()} ({IP_IDS}) - Captura iniciada.")
    return True

def detener_proceso_captura():
    global captura_activa
    if not captura_activa:
        print("[ℹ️] La captura ya está detenida.")
        return False
    
    print("[🛑] Solicitud para detener IDS...")
    captura_activa = False 
    
    if sniffer_thread and sniffer_thread.is_alive():
        print("[⏳] Esperando finalización del hilo de captura (sniffer)...")
        sniffer_thread.join(timeout=5) 
        if sniffer_thread.is_alive():
            print("[⚠️] El hilo de captura (sniffer) no finalizó a tiempo.")
    else:
        print("[ℹ️] Hilo de captura (sniffer) ya no estaba activo o no fue iniciado.")

    if inserter_thread and inserter_thread.is_alive():
        print("[⏳] Esperando finalización del hilo de inserción de paquetes crudos (puede tardar si hay buffer)...")
        inserter_thread.join(timeout=BATCH_SIZE_PAQUETES_CRUDOS * 0.2 + 5) 
        if inserter_thread.is_alive():
            print("[⚠️] El hilo de inserción de paquetes crudos no finalizó a tiempo.")
    else:
        print("[ℹ️] Hilo de inserción de paquetes crudos ya no estaba activo o no fue iniciado.")

    print("[👋] IDS detenido completamente.")
    return True

# ========================
# 🚦 PUNTO DE ENTRADA (Si se ejecuta directamente)
# ========================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test_rules":
        print("[🧪] Modo de prueba de reglas: No se iniciará captura real ni inserción en BD.")
        print("[ℹ️] Implementa la carga de PCAP y el bucle de análisis aquí para probar reglas.")
    elif iniciar_proceso_captura():
        print("[⌨️] IDS en ejecución directa. Presiona Ctrl+C para detener.")
        try:
            while captura_activa: 
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[🚦] Interrupción de teclado detectada. Deteniendo IDS...")
            detener_proceso_captura()
    else:
        print("[💥] No se pudo iniciar el IDS directamente.")