import os
from flask_mail import Mail # Clave para la recuperación de contraseña
from flask import Flask, render_template

# Importación de tus Blueprints (controladores) existentes
from controlador.login import login_bp
from controlador.usuarios import usuarios_bp
from controlador.paquetes import paquetes_bp
from controlador.dispositivos import dispositivos_bp
from controlador.reportes import reportes_bp
from controlador.alertas_acciones_controlador import alertas_acciones_bp

app = Flask(__name__)

# --- Configuración de SECRET_KEY ---
# Esencial para la seguridad de las sesiones y la generación de tokens seguros
# (que se usan a menudo en los enlaces de recuperación de contraseña).
app.secret_key = os.getenv("FLASK_SECRET_KEY", "una_clave_secreta_muy_larga_y_compleja_y_segura")
# ¡ADVERTENCIA! Para producción, usa una variable de entorno (FLASK_SECRET_KEY) con una clave fuerte y única.

# --- Configuración de Flask-Mail (ESENCIAL PARA RECUPERAR CONTRASEÑA POR EMAIL) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'mbejarano844@gmail.com' # Tu email desde donde se enviarán los correos
# ¡MUY IMPORTANTE PARA GMAIL!
# Si tienes la verificación en dos pasos (2FA) activada:
#   DEBES generar una "Contraseña de aplicación" en la configuración de seguridad de Google
#   y usar esa contraseña aquí. No uses tu contraseña normal de Gmail.
#   Visita: https://myaccount.google.com/apppasswords
# Si NO tienes 2FA (menos seguro): puedes usar tu contraseña normal.
app.config['MAIL_PASSWORD'] = 'drtx xgur qjgx udzv' # Tu contraseña de aplicación de Gmail o tu contraseña normal
app.config['MAIL_DEFAULT_SENDER'] = 'mbejarano844@gmail.com' # Email que aparecerá como remitente

mail = Mail(app) # Inicializa Flask-Mail con tu aplicación Flask

# --- Registrar Blueprints ---
# Aquí se registran los diferentes módulos de tu aplicación.
# El blueprint 'login_bp' (o uno similar) probablemente contendrá la lógica
# para solicitar el reseteo de contraseña y manejar el formulario de nueva contraseña.
app.register_blueprint(login_bp) # Probablemente maneje la recuperación de contraseña
app.register_blueprint(usuarios_bp)
app.register_blueprint(paquetes_bp)
app.register_blueprint(dispositivos_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(alertas_acciones_bp)

# Ruta de ejemplo que tenías (puedes mantenerla o eliminarla si no es relevante)
@app.route('/dashboard_reportes')
def mostrar_dashboard():
    return render_template('reporte.html')

from datetime import datetime

@app.context_processor
def utility_processor():
    return dict(now=datetime.utcnow)

if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    # El puerto ahora es 5001 según tu última versión.
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)