from flask import Flask
from controlador.login import login_bp, sistema_bp, eventos_bp
from controlador.usuarios import usuarios_bp
from controlador.paquetes import paquetes_bp
from controlador.dispositivos import dispositivos_bp

app = Flask(__name__)
app.secret_key = 'mi_clave_super_secreta_123'

# Registrar Blueprints
app.register_blueprint(eventos_bp)
app.register_blueprint(sistema_bp)
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(paquetes_bp)
app.register_blueprint(dispositivos_bp)

if __name__ == "__main__":
    app.run(debug=True)
