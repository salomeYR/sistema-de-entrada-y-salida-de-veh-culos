from datetime import datetime
from app import db


class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    vehiculos = db.relationship("Vehiculo", backref="usuario")


class Vehiculo(db.Model):
    __tablename__ = "vehiculo"
    placa = db.Column(db.String(10), primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # carro / moto
    mensualidad_vence = db.Column(db.Date, nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)


class Celda(db.Model):
    __tablename__ = "celda"
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # carro / moto
    ocupada = db.Column(db.Boolean, default=False, nullable=False)


class RegistroAcceso(db.Model):
    __tablename__ = "registro_acceso"
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), db.ForeignKey("vehiculo.placa"), nullable=False)
    id_celda = db.Column(db.Integer, db.ForeignKey("celda.id"), nullable=False)
    fecha_entrada = db.Column(db.DateTime, default=datetime.now, nullable=False)
    fecha_salida = db.Column(db.DateTime, nullable=True)  # None = sigue dentro
    vehiculo = db.relationship("Vehiculo")
    celda = db.relationship("Celda")


class Novedad(db.Model):
    __tablename__ = "novedad"
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), db.ForeignKey("vehiculo.placa"), nullable=False)
    descripcion = db.Column(db.String(300), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now, nullable=False)
    vehiculo = db.relationship("Vehiculo")