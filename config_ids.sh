#!/bin/bash

echo "🚀 Configurando la máquina Kali para actuar como IDS/IPS (configuración temporal para sesión)..."
echo "----------------------------------------------------------------------"

# 1. Habilitar IP Forwarding (Temporal para la sesión actual)
echo "[Paso 1/4] 🔄 Habilitando IP Forwarding para IPv4..."
if echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null; then
    # Verificar que realmente se cambió
    if [[ "$(cat /proc/sys/net/ipv4/ip_forward)" == "1" ]]; then
        echo "✅ IP Forwarding IPv4 habilitado."
    else
        echo "❌ Error: No se pudo cambiar /proc/sys/net/ipv4/ip_forward a 1."
        exit 1
    fi
else
    echo "❌ Error ejecutando el comando para IP Forwarding IPv4. ¿Permisos?"
    exit 1
fi

echo "[Paso 2/4] 🔄 Habilitando IP Forwarding para IPv6..."
if echo 1 | sudo tee /proc/sys/net/ipv6/conf/all/forwarding > /dev/null; then
    if [[ "$(cat /proc/sys/net/ipv6/conf/all/forwarding)" == "1" ]]; then
        echo "✅ IP Forwarding IPv6 habilitado."
    else
        echo "❌ Error: No se pudo cambiar /proc/sys/net/ipv6/conf/all/forwarding a 1."
        # No salimos necesariamente, podría seguir funcionando para IPv4
    fi
else
    echo "❌ Error ejecutando el comando para IP Forwarding IPv6. ¿Permisos?"
fi

# 2. Limpiar reglas existentes en la cadena FORWARD (Opcional, pero bueno para empezar limpio)
echo "[Paso 3/4] 🧹 Limpiando y estableciendo política FORWARD a ACCEPT para iptables (IPv4)..."
if sudo iptables -F FORWARD && sudo iptables -P FORWARD ACCEPT; then
    echo "✅ Cadena FORWARD de iptables limpiada y política establecida en ACCEPT."
else
    echo "❌ Error con iptables (IPv4). Verifica los permisos y si iptables está instalado."
    exit 1
fi

echo "[Paso 4/4] 🧹 Limpiando y estableciendo política FORWARD a ACCEPT para ip6tables (IPv6)..."
if sudo ip6tables -F FORWARD && sudo ip6tables -P FORWARD ACCEPT; then
    echo "✅ Cadena FORWARD de ip6tables limpiada y política establecida en ACCEPT."
else
    echo "❌ Error con ip6tables (IPv6). Verifica los permisos y si ip6tables está instalado."
    # No salimos necesariamente, podría seguir funcionando para IPv4
fi

echo "----------------------------------------------------------------------"
echo "🎉 ¡Configuración temporal de red aplicada para la sesión!"
echo "   Estas configuraciones se perderán al reiniciar."
echo "   (Si instalaste 'iptables-persistent' y guardaste, las políticas de firewall podrían ser más persistentes)."
echo "   Ahora puedes ejecutar tu aplicación Flask IDS con sudo."
echo ""
echo "👉 Para verificar IP Forwarding IPv4: cat /proc/sys/net/ipv4/ip_forward (debe ser 1)"
echo "👉 Para verificar IP Forwarding IPv6: cat /proc/sys/net/ipv6/conf/all/forwarding (debe ser 1)"
echo "👉 Para ver política FORWARD de iptables: sudo iptables -L FORWARD -n -v | grep policy"
echo "👉 Para ver política FORWARD de ip6tables: sudo ip6tables -L FORWARD -n -v | grep policy"
echo "----------------------------------------------------------------------"