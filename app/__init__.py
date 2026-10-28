from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "autos-colombia-clave"
    # Para MySQL cambia por:
    # mysql+pymysql://root:CLAVE@localhost/autos_colombia
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parqueadero.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.controllers.registro_controller import bp
    app.register_blueprint(bp)

    with app.app_context():
        from app import models  # noqa
        db.create_all()

    return app