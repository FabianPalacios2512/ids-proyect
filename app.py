import os
from flask import Flask
from controlador.login import login_bp, sistema_bp, eventos_bp
from controlador.usuarios import usuarios_bp
from controlador.paquetes import paquetes_bp
from controlador.dispositivos import dispositivos_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave_por_defecto_segura")

# Registrar Blueprints (orden opcional por claridad)
app.register_blueprint(sistema_bp)
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(paquetes_bp)
app.register_blueprint(dispositivos_bp)
app.register_blueprint(eventos_bp)

if __name__ == "__main__":
    # threaded=True permite manejar varias peticiones concurrentes
    app.run(debug=False, threaded=True)
