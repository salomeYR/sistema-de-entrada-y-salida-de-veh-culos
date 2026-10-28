from datetime import datetime, date, timedelta
from app import db
from app.models import Vehiculo, Celda, RegistroAcceso, Novedad


class ReglaNegocioError(Exception):
    """Se lanza cuando se incumple una regla del negocio."""


def celdas_libres():
    return Celda.query.filter_by(ocupada=False).all()


def registrar_entrada(placa, id_celda):
    placa = placa.strip().upper()
    vehiculo = db.session.get(Vehiculo, placa)
    if not vehiculo:
        raise ReglaNegocioError("El vehículo no está registrado.")
    if vehiculo.mensualidad_vence < date.today():
        raise ReglaNegocioError("La mensualidad del vehículo está vencida.")
    if RegistroAcceso.query.filter_by(placa=placa, fecha_salida=None).first():
        raise ReglaNegocioError("El vehículo ya se encuentra dentro del parqueadero.")

    celda = db.session.get(Celda, id_celda)
    if not celda:
        raise ReglaNegocioError("La celda no existe.")
    if celda.ocupada:
        raise ReglaNegocioError("La celda seleccionada está ocupada.")
    if celda.tipo != vehiculo.tipo:
        raise ReglaNegocioError("La celda no corresponde al tipo de vehículo.")

    registro = RegistroAcceso(placa=placa, id_celda=celda.id)
    celda.ocupada = True
    db.session.add(registro)
    db.session.commit()
    return registro


def registrar_salida(placa):
    placa = placa.strip().upper()
    registro = RegistroAcceso.query.filter_by(placa=placa, fecha_salida=None).first()
    if not registro:
        raise ReglaNegocioError("No hay una entrada activa para esa placa.")
    registro.fecha_salida = datetime.now()
    registro.celda.ocupada = False
    db.session.commit()
    return registro


def vehiculos_dentro():
    return RegistroAcceso.query.filter_by(fecha_salida=None).all()


def registrar_novedad(placa, descripcion):
    placa = placa.strip().upper()
    if not db.session.get(Vehiculo, placa):
        raise ReglaNegocioError("El vehículo no está registrado.")
    if not descripcion.strip():
        raise ReglaNegocioError("La descripción es obligatoria.")
    novedad = Novedad(placa=placa, descripcion=descripcion.strip())
    db.session.add(novedad)
    db.session.commit()
    return novedad


def historial(placa=None, fecha=None):
    q = RegistroAcceso.query
    if placa:
        q = q.filter(RegistroAcceso.placa == placa.strip().upper())
    if fecha:
        inicio = datetime.strptime(fecha, "%Y-%m-%d")
        q = q.filter(RegistroAcceso.fecha_entrada >= inicio,
                     RegistroAcceso.fecha_entrada < inicio + timedelta(days=1))
    return q.order_by(RegistroAcceso.fecha_entrada.desc()).all()


def novedades():
    return Novedad.query.order_by(Novedad.fecha.desc()).all()