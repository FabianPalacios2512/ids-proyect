from scapy.all import sniff, IP, TCP, UDP, Ether
import mariadb
import threading
import time
import sys
import socket
from datetime import datetime, timedelta
from collections import defaultdict

# ========================
# 🔌 CONEXIÓN A MARIADB
# ========================
def conectar_db():
    while True:
        try:
            conn = mariadb.connect(
                host="localhost",
                user="root",
                password="1234",
                database="ids_proyect",
                autocommit=True
            )
            print("[✅] Conectado a la base de datos.")
            return conn
        except mariadb.Error as e:
            print(f"[❌] Error conectando a MariaDB: {e}. Reintentando en 5s...")
            time.sleep(5)

# ========================
# ⚙️ VARIABLES GLOBALES
# ========================
buffer_lock = threading.Lock()
paquetes_buffer = []
eventos_recientes = defaultdict(lambda: datetime.min)  # evita repetidos
BATCH_SIZE = 100
captura_activa = True

# Obtener la dirección IP local del IDS
def obtener_ip_local():
    try:
        # Crea un socket para determinar la IP local preferida
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except Exception as e:
        print(f"[⚠️] Error al obtener IP local: {e}")
        return "127.0.0.1"  # Fallback a localhost

# IP del sistema IDS (esta máquina)
IP_IDS = obtener_ip_local()
print(f"[ℹ️] IP del sistema IDS: {IP_IDS}")

# ========================
# 🧠 REGISTRO DE EVENTOS
# ========================
def registrar_evento(tipo, descripcion, ip_origen, nivel, detalles, 
                     ip_destino=None, mac_origen=None, mac_destino=None,
                     so_origen=None, puerto_origen=None, puerto_destino=None, protocolo=None):
    
    ahora = datetime.now()
    # Evitar duplicados del mismo tipo desde la misma IP en los últimos 10 minutos
    if ahora - eventos_recientes[(ip_origen, tipo)] < timedelta(minutes=10):
        print(f"[{tipo}] Evento ya registrado recientemente desde {ip_origen}, se ignora.")
        return
    
    eventos_recientes[(ip_origen, tipo)] = ahora
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO eventos_seguridad (
                tipo, descripcion, ip_origen, ip_destino, mac_origen, mac_destino,
                so_origen, puerto_origen, puerto_destino, protocolo,
                nivel, fecha, estado_alerta, estado_evento, detalles, repeticiones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'nueva', 'activo', ?, 1)
        """, (
            tipo, descripcion, ip_origen, ip_destino, mac_origen, mac_destino,
            so_origen, puerto_origen, puerto_destino, protocolo,
            nivel, ahora, detalles
        ))
        print(f"[{tipo}] Evento registrado: {ip_origen} → {ip_destino}")
    except mariadb.Error as e:
        print(f"[⚠️] Error registrando evento en la base de datos: {e}")
    finally:
        conn.close()

# ========================
# 🔍 ANÁLISIS DE REGLAS
# ========================
def analizar_reglas(paquete):
    if not paquete.haslayer(IP):
        return

    ip_origen = paquete[IP].src
    ip_destino = paquete[IP].dst
    ttl = paquete[IP].ttl
    protocolo = paquete[IP].proto
    puerto_origen = paquete.sport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None
    puerto_destino = paquete.dport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None
    mac_origen = paquete[Ether].src if paquete.haslayer(Ether) else None
    mac_destino = paquete[Ether].dst if paquete.haslayer(Ether) else None
    flags = paquete.sprintf("%TCP.flags%") if paquete.haslayer(TCP) else ""
    tamano = len(paquete)
    payload = str(bytes(paquete))[:100]
    
    # Lista completa de protocolos comunes
    protocolos_comunes = {
        1: "ICMP", 6: "TCP", 17: "UDP", 2: "IGMP", 
        47: "GRE", 50: "ESP", 51: "AH", 
        88: "EIGRP", 89: "OSPF", 103: "PIM", 112: "VRRP"
    }
    nombre_protocolo = protocolos_comunes.get(protocolo, f"Desconocido ({protocolo})")
    
    # Determinar sistema operativo por TTL
    so_origen = "Windows" if ttl >= 120 else "Linux/Unix" if ttl >= 60 else "Otro" if ttl >= 30 else "Desconocido"

    detalles = (
        f"IP destino: {ip_destino} | MAC origen: {mac_origen} | MAC destino: {mac_destino} | "
        f"Puerto origen: {puerto_origen} | Puerto destino: {puerto_destino} | "
        f"Protocolo: {nombre_protocolo} | TTL: {ttl} | Flags: {flags} | "
        f"Tamaño: {tamano} bytes | Payload: {payload}"
    )

    # IMPORTANTE: NO ignoramos eventos basados en IP origen/destino
    # Solo ignoramos eventos específicos generados por operaciones normales
    # como escaneos legítimos desde el IDS

    # Evitar alertas de escaneo de red cuando el origen es el IDS
    es_escaneo_legitimo = False
    if ip_origen == IP_IDS:
        # Si es un escaneo típico desde el IDS, lo marcamos como legítimo
        if (paquete.haslayer(TCP) and flags == "S" and 
            puerto_destino in [80, 443, 22, 21, 23, 25, 53]):
            es_escaneo_legitimo = True
    
    # =====================
    # 🔔 REGLAS DE DETECCIÓN
    # =====================
    
    # 1. Detección de SYN Flood (ataques de denegación de servicio)
    if (paquete.haslayer(TCP) and flags == "S" and 
        puerto_destino in [80, 443, 8080, 22, 21, 25, 3389] and 
        not es_escaneo_legitimo):
        registrar_evento("SYN Flood", "Posible ataque de SYN flood detectado", ip_origen, "Alto", detalles,
                      ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 2. Escaneo de puertos - mejorado para detectar patrones específicos
    if paquete.haslayer(TCP) and not es_escaneo_legitimo:
        # Escaneo SYN 
        if flags == "S" and puerto_destino and puerto_destino < 1024:
            registrar_evento("Port Scan", "Escaneo de puertos SYN detectado", ip_origen, "Medio", detalles,
                          ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
        # Escaneo FIN
        elif flags == "F" and puerto_destino < 1024:
            registrar_evento("Stealth Scan", "Escaneo sigiloso FIN detectado", ip_origen, "Alto", detalles,
                          ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
        # Escaneo XMAS
        elif flags == "FPU" and puerto_destino < 1024:
            registrar_evento("XMAS Scan", "Escaneo XMAS detectado", ip_origen, "Alto", detalles,
                          ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
        # Escaneo NULL
        elif flags == "" and paquete.haslayer(TCP) and puerto_destino < 1024:
            registrar_evento("NULL Scan", "Escaneo NULL detectado", ip_origen, "Alto", detalles,
                          ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 3. Acceso a puertos críticos - expandido con más puertos
    puertos_criticos = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 
        53: "DNS", 67: "DHCP", 80: "HTTP", 110: "POP3", 
        139: "NetBIOS", 143: "IMAP", 161: "SNMP", 389: "LDAP", 
        445: "SMB", 1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 
        3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-ALT", 
        27017: "MongoDB"
    }
    
    if (puerto_destino in puertos_criticos and paquete.haslayer(TCP) and 
        flags == "S" and not es_escaneo_legitimo):
        servicio = puertos_criticos[puerto_destino]
        registrar_evento(
            f"Acceso {servicio}", 
            f"Intento de conexión al servicio {servicio}", 
            ip_origen, "Medio", detalles,
            ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo
        )

    # 4. Detección de TTL anormal o modificado
    #if ttl < 3:
     #   registrar_evento("TTL sospechoso", "TTL extremadamente bajo detectado (posible manipulación)", 
      #                 ip_origen, "Medio", detalles,
       #                ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
    
    # 5. Protocolo no común - solo alertar si realmente es desconocido
    if protocolo not in protocolos_comunes:
        registrar_evento("Protocolo inusual", f"Protocolo no común detectado: {protocolo}", 
                       ip_origen, "Bajo", detalles,
                       ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 6. Paquete ICMP sospechoso (posible ping de la muerte o similar)
    if paquete.haslayer(IP) and protocolo == 1 and tamano > 1470:
        registrar_evento("ICMP grande", "Paquete ICMP anormalmente grande detectado", 
                      ip_origen, "Medio", detalles,
                      ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 7. Detección de tráfico fragmentado (posible evasión de IDS)
    if paquete[IP].flags & 1 or paquete[IP].frag != 0:
        registrar_evento("Fragmentación IP", "Paquete fragmentado detectado (posible evasión)", 
                       ip_origen, "Medio", detalles,
                       ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    

    # 9. Detección de posible malware por patrones en el payload
    patrones_malware = [
        b"exec(", b"system(", b"shell_exec", b"powershell -enc", 
        b"cmd.exe", b"wget http", b"eval(base64", b"frombase64string",
        b"passthru", b"rm -rf", b"format c:", b"rundll32", b"cmd /c",
        b"meterpreter", b"reverse_tcp", b"reverse_http"
    ]
    
    if payload:
        payload_bytes = payload.lower().encode() if isinstance(payload, str) else payload.lower()
        for patron in patrones_malware:
            if patron.lower() in payload_bytes:
                registrar_evento("Payload malicioso", f"Patrón sospechoso en payload: {patron.decode()}", 
                              ip_origen, "Alto", detalles,
                              ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
                break

    # 10. Detección de conexiones salientes a puertos sospechosos
    puertos_salida_sospechosos = [4444, 1337, 31337, 6667, 6666, 8888, 5555, 9999, 4242]
    if (puerto_destino in puertos_salida_sospechosos and 
        not (ip_origen == IP_IDS or ip_destino == IP_IDS)):  # Ignorar tráfico del propio IDS
        registrar_evento("Puerto C&C", f"Conexión saliente a puerto potencial de C&C: {puerto_destino}", 
                      ip_origen, "Alto", detalles,
                      ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
    
    # 11. Detección de ataques de fuerza bruta SSH/FTP/RDP
    if (paquete.haslayer(TCP) and flags == "S" and 
        puerto_destino in [22, 21, 3389] and 
        not es_escaneo_legitimo):
        registrar_evento("Fuerza Bruta", f"Posible ataque de fuerza bruta a {puertos_criticos.get(puerto_destino, 'servicio')}", 
                       ip_origen, "Alto", detalles,
                       ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)
    
    # 12. Detección de comunicaciones DNS sospechosas (posibles túneles DNS)
    if protocolo == 17 and (puerto_origen == 53 or puerto_destino == 53) and tamano > 300:
        registrar_evento("DNS sospechoso", "Paquete DNS anormalmente grande (posible túnel)", 
                      ip_origen, "Medio", detalles,
                      ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

# ========================
# 📡 PROCESAR PAQUETE
# ========================
def procesar_paquete(paquete):
    try:
        if not paquete.haslayer(IP):
            return

        ip_origen = paquete[IP].src
        ip_destino = paquete[IP].dst
        mac_origen = paquete[Ether].src if paquete.haslayer(Ether) else None
        mac_destino = paquete[Ether].dst if paquete.haslayer(Ether) else None
        puerto_origen = paquete.sport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None
        puerto_destino = paquete.dport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None
        protocolo = paquete[IP].proto
        ttl = paquete[IP].ttl
        flags_tcp = paquete.sprintf("%TCP.flags%") if paquete.haslayer(TCP) else None
        payload = str(bytes(paquete))[:100]
        nombre_protocolo = {6: "TCP", 17: "UDP", 1: "ICMP"}.get(protocolo, f"Desconocido ({protocolo})")

        with buffer_lock:
            if len(paquetes_buffer) < 10000:  # Evita explosión de memoria
                paquetes_buffer.append((
                    ip_origen, ip_destino, mac_origen, mac_destino, puerto_origen,
                    puerto_destino, nombre_protocolo, len(paquete), ttl, flags_tcp,
                    payload, nombre_protocolo, flags_tcp, payload
                ))

        analizar_reglas(paquete)
    except Exception as e:
        print(f"[⚠️] Error procesando paquete: {e}")

# ========================
# 💾 INSERCIÓN EN LOTES
# ========================
def insertar_paquetes():
    while True:
        time.sleep(2)
        with buffer_lock:
            if not paquetes_buffer:
                continue
            lote = paquetes_buffer[:BATCH_SIZE]
            del paquetes_buffer[:BATCH_SIZE]

        conn = conectar_db()
        try:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO escanear_red (
                    iporigen, ipdestino, mac_origen, mac_destino, 
                    puerto_origen, puerto_destino, protocolo, tamano, ttl, 
                    flags_tcp, payload, protocolo_nombre, descripcion_flags, descripcion_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, lote)
            print(f"[💾] {len(lote)} paquetes insertados.")
        except mariadb.Error as e:
            print(f"[⚠️] Error al insertar paquetes: {e}")
        finally:
            conn.close()

# ========================
# ▶️ INICIAR ESCANEO
# ========================
def iniciar_escaneo():
    print("[🚀] Iniciando escaneo de red...")
    threading.Thread(target=lambda: sniff(prn=procesar_paquete, store=False), daemon=True).start()
    threading.Thread(target=insertar_paquetes, daemon=True).start()

if __name__ == "__main__":
    iniciar_escaneo()
    print("[⌛] Capturando paquetes. Presiona Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Captura detenida manualmente.")
        captura_activa = False