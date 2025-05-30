import os
from flask_mail import Mail
from flask import Flask, render_template

# Importación de tus Blueprints (controladores) existentes
# MODIFICACIÓN AQUÍ: Añade sistema_bp y eventos_bp
from controlador.login import login_bp, sistema_bp, eventos_bp # <--- ¡IMPORTANTE!
from controlador.usuarios import usuarios_bp
from controlador.paquetes import paquetes_bp
from controlador.dispositivos import dispositivos_bp
from controlador.reportes import reportes_bp
from controlador.alertas_acciones_controlador import alertas_acciones_bp

app = Flask(__name__)

# --- Configuración de SECRET_KEY ---
app.secret_key = os.getenv("FLASK_SECRET_KEY", "una_clave_secreta_muy_larga_y_compleja_y_segura")

# --- Configuración de Flask-Mail ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'mbejarano844@gmail.com'
app.config['MAIL_PASSWORD'] = 'drtx xgur qjgx udzv' # Considera usar variables de entorno también para esto
app.config['MAIL_DEFAULT_SENDER'] = 'mbejarano844@gmail.com'

mail = Mail(app)

# --- Registrar Blueprints ---
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(paquetes_bp)
app.register_blueprint(dispositivos_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(alertas_acciones_bp)

# MODIFICACIÓN AQUÍ: Registra los blueprints que faltaban
app.register_blueprint(sistema_bp) # <--- ¡AÑADIDO!
app.register_blueprint(eventos_bp) # <--- ¡AÑADIDO!


@app.route('/dashboard_reportes')
def mostrar_dashboard():
    return render_template('reporte.html')

from datetime import datetime

@app.context_processor
def utility_processor():
    return dict(now=datetime.utcnow)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)