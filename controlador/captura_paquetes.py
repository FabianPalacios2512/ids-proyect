from scapy.all import sniff, IP, TCP, UDP, Ether
import mariadb
import threading
import time
import sys
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

# ========================
# 🧠 REGISTRO DE EVENTOS
# ========================
def registrar_evento(tipo, descripcion, ip_origen, nivel, detalles, 
                     ip_destino=None, mac_origen=None, mac_destino=None,
                     so_origen=None, puerto_origen=None, puerto_destino=None, protocolo=None):
    
    ahora = datetime.now()
    if ahora - eventos_recientes[ip_origen, tipo] < timedelta(minutes=10):
        print(f"[{tipo}] Evento ya registrado recientemente desde {ip_origen}, se ignora.")
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
        print(f"[{tipo}] Evento registrado: {ip_origen}")
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
    nombre_protocolo = {6: "TCP", 17: "UDP", 1: "ICMP"}.get(protocolo, f"Desconocido ({protocolo})")
    so_origen = "Windows" if ttl >= 120 else "Linux" if ttl >= 60 else "Desconocido"

    detalles = (
        f"IP destino: {ip_destino} | MAC origen: {mac_origen} | MAC destino: {mac_destino} | "
        f"Puerto origen: {puerto_origen} | Puerto destino: {puerto_destino} | "
        f"Protocolo: {nombre_protocolo} | TTL: {ttl} | Flags: {flags} | "
        f"Tamaño: {tamano} bytes | Payload: {payload}"
    )

    if flags == "S":
        registrar_evento("SYN Flood", "Posible SYN flood detectado", ip_origen, "Alto", detalles,
                         ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    if flags == "S" and puerto_destino and 1 <= puerto_destino <= 1024:
        registrar_evento("Scan", "Escaneo de puertos detectado", ip_origen, "Medio", detalles,
                         ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    if puerto_destino in [21, 22, 23, 445, 139, 3389]:
        registrar_evento("Acceso sospechoso", "Acceso a puerto crítico", ip_origen, "Medio", detalles,
                         ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    if ttl < 10:
        registrar_evento("TTL sospechoso", "TTL bajo detectado", ip_origen, "Bajo", detalles,
                         ip_destino, mac_origen, mac_destino, so_origen, puerto_origen, puerto_destino, nombre_protocolo)

    if protocolo not in [1, 6, 17]:
        registrar_evento("Protocolo sospechoso", "Protocolo no común detectado", ip_origen, "Medio", detalles,
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
