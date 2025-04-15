from scapy.all import sniff, IP, TCP, UDP, Ether
import mariadb
import threading
import time
import sys
from datetime import datetime

# ==========================
# 🔌 Conexión a MariaDB
# ==========================
try:
    conn = mariadb.connect(
        host="localhost",
        user="root",
        password="1234",
        database="ids_proyect"
    )
    cursor = conn.cursor()
    print("[✅] Conectado a la base de datos.")
except mariadb.Error as e:
    print(f"[❌] Error conectando a MariaDB: {e}")
    sys.exit(1)

# ==========================
# 📤 Buffer y control
# ==========================
paquetes_buffer = []
BATCH_SIZE = 1
captura_activa = False
hilo_captura = None

# ==========================
# 🧠 Registro de eventos
# ==========================
from datetime import datetime, timedelta

def registrar_evento(tipo, descripcion, ip_origen, nivel, estado, detalles, db_connection):
    cursor = db_connection.cursor()

    # Verificar si ya existe un evento similar en los últimos 10 minutos
    tiempo_limite = datetime.now() - timedelta(minutes=10)
    query = """
        SELECT id_evento, fecha FROM eventos_seguridad 
        WHERE tipo = %s AND ip_origen = %s AND estado = 'activo'
        ORDER BY fecha DESC LIMIT 1
    """
    cursor.execute(query, (tipo, ip_origen))
    resultado = cursor.fetchone()

    if resultado:
        id_evento_existente, fecha_evento = resultado

        if fecha_evento > tiempo_limite:
            print(f"[{tipo}] Evento ya registrado recientemente desde {ip_origen}, se ignora.")
            return  # Ya hay un evento reciente igual, no lo volvemos a registrar

        else:
            # Si el evento es viejo, lo actualizamos
            update_query = """
                UPDATE eventos_seguridad SET fecha = %s, descripcion = %s, nivel = %s, detalles = %s 
                WHERE id_evento = %s
            """
            cursor.execute(update_query, (datetime.now(), descripcion, nivel, detalles, id_evento_existente))
            db_connection.commit()
            print(f"[{tipo}] Evento actualizado desde {ip_origen}.")
            return

    # Insertar nuevo evento si no existe
    insert_query = """
        INSERT INTO eventos_seguridad (tipo, descripcion, ip_origen, nivel, fecha, estado, detalles)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (tipo, descripcion, ip_origen, nivel, datetime.now(), estado, detalles))
    db_connection.commit()
    print(f"[{tipo}] Nuevo evento registrado desde {ip_origen}.")


# ==========================
# 🔍 Reglas de seguridad
# ==========================
def analizar_reglas(paquete):
    if not paquete.haslayer(IP):
        return

    ip_origen = paquete[IP].src
    ip_destino = paquete[IP].dst
    ttl = paquete[IP].ttl
    protocolo = paquete[IP].proto
    puerto_origen = paquete.sport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None
    puerto_destino = paquete.dport if paquete.haslayer(TCP) or paquete.haslayer(UDP) else None
    flags = paquete.sprintf("%TCP.flags%") if paquete.haslayer(TCP) else ""

    # 🚨 Regla 1: SYN flood
    if flags == "S":
        registrar_evento(
            descripcion="Posible SYN flood detectado",
            ip_origen=ip_origen,
            ip_destino=ip_destino,
            tipo="SYN Flood",
            nivel="Alto",
            estado_alerta="nueva",
            detalles="Demasiados paquetes SYN sin respuesta",
            puerto_origen=puerto_origen,
            puerto_destino=puerto_destino,
            protocolo="TCP"
        )

    # 🚨 Regla 2: Escaneo de puertos
    if flags == "S" and puerto_destino in range(1, 1025):
        registrar_evento(
            descripcion="Escaneo de puertos detectado",
            ip_origen=ip_origen,
            ip_destino=ip_destino,
            tipo="Scan",
            nivel="Medio",
            estado_alerta="nueva",
            detalles=f"Puerto escaneado: {puerto_destino}",
            puerto_destino=puerto_destino,
            protocolo="TCP"
        )

    # 🚨 Regla 3: Acceso a puertos críticos
    if puerto_destino in [22, 23, 21, 3389, 445, 139]:
        registrar_evento(
            descripcion="Acceso a puerto crítico",
            ip_origen=ip_origen,
            ip_destino=ip_destino,
            tipo="Acceso sospechoso",
            nivel="Medio",
            estado_alerta="nueva",
            detalles=f"Intento de conexión al puerto {puerto_destino}",
            puerto_destino=puerto_destino,
            protocolo="TCP/UDP"
        )

    # 🚨 Regla 4: TTL bajo (posible evasión)
    if ttl < 10:
        registrar_evento(
            descripcion="TTL bajo detectado",
            ip_origen=ip_origen,
            ip_destino=ip_destino,
            tipo="TTL sospechoso",
            nivel="Bajo",
            estado_alerta="nueva",
            detalles=f"TTL: {ttl}",
            protocolo="IP"
        )

    # 🚨 Regla 5: Protocolo raro
    if protocolo not in [1, 6, 17]:  # ICMP, TCP, UDP
        registrar_evento(
            descripcion="Protocolo no común detectado",
            ip_origen=ip_origen,
            ip_destino=ip_destino,
            tipo="Protocolo sospechoso",
            nivel="Medio",
            estado_alerta="nueva",
            detalles=f"Protocolo número: {protocolo}",
            protocolo=f"ID:{protocolo}"
        )

# ==========================
# 📡 Procesamiento de paquetes
# ==========================
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
        tamano = len(paquete)
        ttl = paquete[IP].ttl
        flags_tcp = paquete.sprintf("%TCP.flags%") if paquete.haslayer(TCP) else None
        payload = str(paquete.payload)[:100]

        nombre_protocolo = {6: "TCP", 17: "UDP", 1: "ICMP"}.get(protocolo, f"Desconocido ({protocolo})")

        paquetes_buffer.append((
            ip_origen, ip_destino, mac_origen, mac_destino, puerto_origen,
            puerto_destino, nombre_protocolo, tamano, ttl, flags_tcp, payload,
            nombre_protocolo, flags_tcp, payload
        ))

        print(f"[📡] {ip_origen} → {ip_destino} | {nombre_protocolo} | {tamano} bytes")

        analizar_reglas(paquete)  # Analizar el paquete con las reglas

    except Exception as e:
        print(f"[⚠️] Error procesando paquete: {e}")

# ==========================
# 💾 Inserción en lotes
# ==========================
def insertar_paquetes():
    global paquetes_buffer
    while True:
        time.sleep(2)
        if paquetes_buffer:
            try:
                cursor.executemany("""
                INSERT INTO escanear_red (
                    iporigen, ipdestino, mac_origen, mac_destino, 
                    puerto_origen, puerto_destino, protocolo, tamano, ttl, 
                    flags_tcp, payload, protocolo_nombre, descripcion_flags, descripcion_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, paquetes_buffer)

                conn.commit()
                print(f"[📥] {len(paquetes_buffer)} paquetes insertados.")
                paquetes_buffer = []
            except Exception as e:
                print(f"[⚠️] Error al insertar paquetes: {e}")

threading.Thread(target=insertar_paquetes, daemon=True).start()

# ==========================
# ▶️ Control de escaneo
# ==========================
def iniciar_escaneo_red():
    global captura_activa, hilo_captura
    if not captura_activa:
        print("[🚀] Iniciando captura de paquetes...")
        captura_activa = True
        hilo_captura = threading.Thread(target=lambda: sniff(prn=procesar_paquete, store=False), daemon=True)
        hilo_captura.start()

if __name__ == "__main__":
    iniciar_escaneo_red()
    print("[⌛] Capturando... presiona Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Captura detenida manualmente.")
