
import os
 
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
 
db = SQLAlchemy()
 
 
def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "autos-colombia-clave")
    # Para MySQL cambia por:
    # mysql+pymysql://root:CLAVE@localhost/autos_colombia
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parqueadero.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:  # permite probar con una base de datos temporal
        app.config.update(test_config)
 
    db.init_app(app)
 
    from app.controllers.registro_controller import bp as registro_bp
    from app.controllers.usuario_controller import bp as usuario_bp
    from app.controllers.celda_controller import bp as celda_bp
 
    app.register_blueprint(registro_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(celda_bp)
 
    with app.app_context():
        from app import models  # noqa
        db.create_all()
 
    return app