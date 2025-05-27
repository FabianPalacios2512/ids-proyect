# controlador/iptables_manager.py
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_firewall_command(command_list):
    """Ejecuta un comando de firewall (iptables o ip6tables) y maneja errores."""
    try:
        logging.info(f"FW_CMD: Ejecutando: {' '.join(command_list)}")
        # El script principal corre con sudo, no necesitamos 'sudo' aquí.
        subprocess.run(command_list, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        stderr_lower = e.stderr.lower()
        if '-D' in command_list and \
           ('no chain/target/match by that name' in stderr_lower or \
            'rule' in stderr_lower and 'doesn.t exist' in stderr_lower or \
            'target specific error' in stderr_lower or \
            'unable to initialize table' in stderr_lower and 'resource temporarily unavailable' in stderr_lower): # A veces iptables da este error si se borra rápido
             logging.warning(f"FW_CMD: No se pudo borrar regla (quizás ya no existía/problema temporal): {' '.join(command_list)}")
             return True 
        logging.error(f"FW_CMD: Error ejecutando {' '.join(command_list)}: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"FW_CMD: Error: El comando '{command_list[0]}' no se encontró.")
        return False
    except Exception as e:
        logging.error(f"FW_CMD: Error inesperado ejecutando {' '.join(command_list)}: {e}")
        return False

# --- Funciones IPv4 ---
def block_ipv4(target_ipv4):
    logging.info(f"IPTABLES: Bloqueando IPv4 {target_ipv4}")
    success1 = run_firewall_command(['iptables', '-I', 'FORWARD', '1', '-s', target_ipv4, '-j', 'DROP'])
    success2 = run_firewall_command(['iptables', '-I', 'FORWARD', '1', '-d', target_ipv4, '-j', 'DROP'])
    return success1 and success2

def unblock_ipv4(target_ipv4):
    logging.info(f"IPTABLES: Desbloqueando IPv4 {target_ipv4}")
    run_firewall_command(['iptables', '-D', 'FORWARD', '-s', target_ipv4, '-j', 'DROP'])
    run_firewall_command(['iptables', '-D', 'FORWARD', '-d', target_ipv4, '-j', 'DROP'])
    return True # Asumimos que la intención es que esté desbloqueado

# --- Funciones IPv6 ---
def block_ipv6(target_ipv6):
    """Bloquea tráfico IPv6. target_ipv6 puede ser link-local o global."""
    logging.info(f"IP6TABLES: Bloqueando IPv6 {target_ipv6}")
    success1 = run_firewall_command(['ip6tables', '-I', 'FORWARD', '1', '-s', target_ipv6, '-j', 'DROP'])
    success2 = run_firewall_command(['ip6tables', '-I', 'FORWARD', '1', '-d', target_ipv6, '-j', 'DROP'])
    return success1 and success2

def unblock_ipv6(target_ipv6):
    logging.info(f"IP6TABLES: Desbloqueando IPv6 {target_ipv6}")
    run_firewall_command(['ip6tables', '-D', 'FORWARD', '-s', target_ipv6, '-j', 'DROP'])
    run_firewall_command(['ip6tables', '-D', 'FORWARD', '-d', target_ipv6, '-j', 'DROP'])
    return True