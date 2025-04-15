from flask import Flask, request, render_template_string
from datetime import datetime
import ipaddress

app = Flask(__name__)

@app.route('/')
def capturar_ip():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    agente = request.headers.get('User-Agent')
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Detectar IPv4 o IPv6
    try:
        ip_obj = ipaddress.ip_address(ip)
        tipo = f"IPv{ip_obj.version}"
    except ValueError:
        tipo = "Desconocida"

    # Guardar IP y navegador
    with open("ips_capturadas.txt", "a") as f:
        f.write(f"{hora} - IP: {ip} ({tipo}) - Navegador: {agente}\n")

    # Mensaje con miedo
    html_mensaje = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Ya te tengo</title>
        <script>
            setTimeout(() => {{
                window.close();
            }}, 5000);  // Cierra después de 8 segundos
        </script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-black text-red-600 flex flex-col items-center justify-center h-screen text-center p-6">
        <h1 class="text-4xl font-bold mb-4 animate-pulse">😈 Ya tengo tus Datos...</h1>
        <p class="text-xl mb-4">IP capturada: <span class="text-white">{ip}</span> ({tipo})</p>
        <p class="text-lg mb-2">Navegador: <span class="text-white">{agente}</span></p>
        <p class="text-xl mt-6 text-red-400">Esto es solo el comienzo....</p>
        <p class="text-sm text-gray-600 mt-10">(Esta página se cerrará automáticamente)</p>
    </body>
    </html>
    """
    return render_template_string(html_mensaje)

if __name__ == '__main__':
    app.run(port=5000)
