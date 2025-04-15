from scapy.all import ARP, Ether, srp

# Define el rango de IP a escanear (ajústalo a tu red)
ip_red = "192.168.0.0/24"

# Crea un paquete ARP envuelto en un paquete Ethernet
arp = ARP(pdst=ip_red)
ether = Ether(dst="ff:ff:ff:ff:ff:ff")
paquete = ether / arp

# Envía el paquete y recibe respuestas
print("[*] Escaneando la red...")
respuestas = srp(paquete, timeout=2, verbose=0)[0]

# Muestra los dispositivos encontrados
print("\nDispositivos encontrados:")
print("IP" + " " * 18 + "MAC")
print("-" * 40)

for enviado, recibido in respuestas:
    print(f"{recibido.psrc:20} {recibido.hwsrc}")

print("\n[✔] Escaneo finalizado.")
