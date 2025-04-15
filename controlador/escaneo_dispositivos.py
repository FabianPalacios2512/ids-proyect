import nmap
import netifaces
from datetime import datetime
from threading import Thread

from modelo.base_datos import obtener_conexion

escaneo_en_progreso = False
hilo_escaneo = None


def obtener_rango_red():
    interfaz = netifaces.gateways()['default'][netifaces.AF_INET][1]
    ip_info = netifaces.ifaddresses(interfaz)[netifaces.AF_INET][0]
    ip = ip_info['addr']
    mascara = ip_info['netmask']
    bits = sum([bin(int(x)).count("1") for x in mascara.split('.')])
    return f"{ip}/{bits}"


def obtener_mac(nm, ip):
    try:
        return nm[ip]['addresses'].get('mac', 'Desconocido')
    except:
        return 'Desconocido'


def obtener_puertos_abiertos(nm, ip):
    puertos = []
    for proto in nm[ip].all_protocols():
        lport = nm[ip][proto].keys()
        for port in sorted(lport):
            state = nm[ip][proto][port]['state']
            if state == 'open':
                puertos.append(str(port))
    return ', '.join(puertos)


def escanear_y_guardar_dispositivos():
    global escaneo_en_progreso
    escaneo_en_progreso = True
    print("[🌐] Iniciando escaneo de red...")
    rango = obtener_rango_red()
    print(f"[🌐] Escaneando red en el rango: {rango}")

    nm = nmap.PortScanner()
    nm.scan(hosts=rango, arguments="-sS -O -T5")

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    dispositivos_actuales = []

    for ip in nm.all_hosts():
        try:
            mac = obtener_mac(nm, ip)
            hostname = nm[ip].hostname() or ""
            sistema_operativo = "Desconocido"
            if 'osmatch' in nm[ip] and len(nm[ip]['osmatch']) > 0:
                sistema_operativo = nm[ip]['osmatch'][0]['name']

            puertos_abiertos = obtener_puertos_abiertos(nm, ip)
            fecha_escaneo = datetime.now()

            dispositivos_actuales.append(mac)

            cursor.execute("""
                SELECT * FROM dispositivos 
                WHERE direccion_ip = %s AND direccion_mac = %s AND puerto = %s
            """, (ip, mac, puertos_abiertos))
            existe = cursor.fetchone()

            if existe:
                cursor.execute("""
                    UPDATE dispositivos 
                    SET estado_dispositivo = 'activo', fecha_escaneo = %s 
                    WHERE id = %s
                """, (fecha_escaneo, existe['id']))
            else:
               cursor.execute("""
    INSERT INTO dispositivos (direccion_ip, direccion_mac, nombre_host, sistema_operativo, puerto, fecha_escaneo, estado_dispositivo) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (ip, mac, hostname, sistema_operativo, puertos_abiertos, fecha_escaneo, 'activo'))



            conexion.commit()

        except Exception as e:
            print(f"[⚠️] Error procesando host {ip}: {e}")

    cursor.execute("SELECT direccion_mac FROM dispositivos WHERE estado_dispositivo = 'activo'")
    registros = cursor.fetchall()
    macs_base = set([d['direccion_mac'] for d in registros])
    macs_detectadas = set(dispositivos_actuales)

    macs_desconectadas = macs_base - macs_detectadas
    for mac in macs_desconectadas:
        cursor.execute("""
            UPDATE dispositivos SET estado_dispositivo = 'inactivo' WHERE direccion_mac = %s
        """, (mac,))
    conexion.commit()

    cursor.close()
    conexion.close()
    print("[✅] Escaneo finalizado y datos guardados.")
    escaneo_en_progreso = False


# === Funciones para integrarlo con Flask ===

def iniciar_escaneo_red():
    global hilo_escaneo
    if not escaneo_en_progreso:
        hilo_escaneo = Thread(target=escanear_y_guardar_dispositivos)
        hilo_escaneo.start()
        return True
    return False


def detener_escaneo_red():
    # En este tipo de escaneo puntual, detener no aplica. Solo se usaría si hacemos un loop continuo.
    return True
