from scapy.all import sniff, IP, TCP, UDP, Ether, ICMP
import mariadb
import threading
import time
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
eventos_recientes = defaultdict(lambda: datetime.min)
BATCH_SIZE = 100
captura_activa = True
contador_icmp = defaultdict(int)
limite_icmp = 50  # límite de paquetes ICMP por IP por minuto

# ========================
# 🧠 REGISTRO DE EVENTOS
# ========================
def registrar_evento(tipo, descripcion, ip_origen, nivel, detalles, 
                     ip_destino=None, mac_origen=None, mac_destino=None,
                     so_origen=None, puerto_origen=None, puerto_destino=None, protocolo=None):
    
    ahora = datetime.now()
    if ahora - eventos_recientes[ip_origen, tipo] < timedelta(minutes=10):
        print(f"[{tipo}] Evento repetido recientemente desde {ip_origen}, se ignora.")
        return

    eventos_recientes[ip_origen, tipo] = ahora
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
        print(f"[{tipo}] Evento registrado desde {ip_origen}")
    except mariadb.Error as e:
        print(f"[⚠️] Error registrando evento: {e}")
    finally:
        conn.close()

# ========================
# 🧠 DETECCIÓN DE AMENAZAS
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
    nombre_protocolo = {6: "TCP", 17: "UDP", 1: "ICMP"}.get(protocolo, f"Desconocido ({protocolo})")
    so_origen = "Windows" if ttl >= 115 else "Linux" if ttl >= 40 else "Desconocido"

    detalles = (
        f"Destino: {ip_destino} | MAC origen: {mac_origen} | MAC destino: {mac_destino} | "
        f"Puerto origen: {puerto_origen} | Puerto destino: {puerto_destino} | "
        f"Protocolo: {nombre_protocolo} | TTL: {ttl} | Flags: {flags} | "
        f"Payload: {payload}"
    )

    # 🎯 Regla 1: SYN Flood
    if flags == "S":
        registrar_evento("SYN Flood", "Sospecha de SYN Flood", ip_origen, "Alto", detalles,
                         ip_destino, mac_origen, mac_destino, so_origen,
                         puerto_origen, puerto_destino, nombre_protocolo)

    # 🎯 Regla 2: Escaneo de puertos conocidos
    if flags == "S" and puerto_destino and 1 <= puerto_destino <= 1024:
        registrar_evento("Port Scan", f"Escaneo de puerto {puerto_destino} detectado", ip_origen,
                         "Medio", detalles, ip_destino, mac_origen, mac_destino,
                         so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 🎯 Regla 3: Acceso a puertos sensibles
    puertos_criticos = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        80: "HTTP", 110: "POP3", 139: "NetBIOS", 143: "IMAP",
        445: "SMB", 3306: "MySQL", 3389: "RDP"
    }
    if puerto_destino in puertos_criticos:
        servicio = puertos_criticos[puerto_destino]
        registrar_evento("Acceso sospechoso", f"Intento de acceso al servicio {servicio} (puerto {puerto_destino})",
                         ip_origen, "Medio", detalles, ip_destino, mac_origen,
                         mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 🎯 Regla 4: TTL extremadamente bajo
    if ttl < 4:
        registrar_evento("TTL sospechoso", "TTL extremadamente bajo, posible manipulación o túnel", ip_origen,
                         "Bajo", detalles, ip_destino, mac_origen, mac_destino,
                         so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 🎯 Regla 5: Protocolo no estándar
    if protocolo not in [1, 6, 17]:
        registrar_evento("Protocolo inusual", f"Protocolo desconocido detectado: {protocolo}", ip_origen,
                         "Medio", detalles, ip_destino, mac_origen, mac_destino,
                         so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 🎯 Regla 6: Exceso de ICMP por minuto
    if paquete.haslayer(ICMP):
        contador_icmp[ip_origen] += 1
        if contador_icmp[ip_origen] > limite_icmp:
            registrar_evento("ICMP Flood", "Alto número de paquetes ICMP detectado", ip_origen,
                             "Alto", detalles, ip_destino, mac_origen, mac_destino,
                             so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    # 🎯 Regla 7: Tráfico DNS inusual
    if puerto_destino == 53 or puerto_origen == 53:
        if not paquete.haslayer(UDP):
            registrar_evento("DNS anómalo", "Tráfico DNS usando protocolo no UDP", ip_origen,
                             "Medio", detalles, ip_destino, mac_origen, mac_destino,
                             so_origen, puerto_origen, puerto_destino, nombre_protocolo)

# ========================
# 🧪 PROCESAR PAQUETE
# ========================
def procesar_paquete(paquete):
    with buffer_lock:
        paquetes_buffer.append(paquete)
        if len(paquetes_buffer) >= BATCH_SIZE:
            lote = paquetes_buffer.copy()
            paquetes_buffer.clear()
            threading.Thread(target=procesar_lote, args=(lote,), daemon=True).start()

def procesar_lote(lote):
    for paquete in lote:
        try:
            analizar_reglas(paquete)
        except Exception as e:
            print(f"[⚠️] Error al analizar paquete: {e}")

# ========================
# 💾 INSERCIÓN PERIÓDICA
# ========================
def insertar_paquetes():
    while captura_activa:
        time.sleep(10)
        with buffer_lock:
            if paquetes_buffer:
                lote = paquetes_buffer.copy()
                paquetes_buffer.clear()
                procesar_lote(lote)

# ========================
# 🚀 INICIO DEL ESCANEO
# ========================
def iniciar_escaneo():
    print("[🚨] Iniciando captura de paquetes...")
    hilo_insertar = threading.Thread(target=insertar_paquetes, daemon=True)
    hilo_insertar.start()
    sniff(prn=procesar_paquete, store=False)

# ========================
# ▶️ MAIN
# ========================
if __name__ == "__main__":
    try:
        iniciar_escaneo()
    except KeyboardInterrupt:
        print("\n[🛑] Captura detenida por el usuario.")
        captura_activa = False
