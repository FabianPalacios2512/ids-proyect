import os
from flask import Flask, render_template # ¡Añadir render_template!
from controlador.login import login_bp, sistema_bp, eventos_bp
from controlador.usuarios import usuarios_bp
from controlador.paquetes import paquetes_bp
from controlador.dispositivos import dispositivos_bp
from controlador.reportes import reportes_bp # <--- ¡IMPORTAR NUESTRO BLUEPRINT!

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave_por_defecto_segura")

# Registrar Blueprints
app.register_blueprint(sistema_bp)
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(paquetes_bp)
app.register_blueprint(dispositivos_bp)
app.register_blueprint(eventos_bp)
app.register_blueprint(reportes_bp) # <--- ¡REGISTRAR NUESTRO BLUEPRINT!

# --- ¡AÑADIR RUTA PARA MOSTRAR EL DASHBOARD! ---
@app.route('/dashboard_reportes')
def mostrar_dashboard():
    # Aquí podrías verificar si el usuario está logueado si es necesario
    return render_template('reporte.html')
# ---------------------------------------------

if __name__ == "__main__":
    # threaded=True permite manejar varias peticiones concurrentes
    # debug=True es útil durante el desarrollo, pero ponlo a False en producción
    app.run(debug=True, threaded=True)