import re
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Usuario, Vehiculo, RegistroAcceso
from app.services.registro_service import ReglaNegocioError

TIPOS = ("carro", "moto")
PATRON_PLACA = {
    "carro": re.compile(r"^[A-Z]{3}\d{3}$"),       # ABC123
    "moto": re.compile(r"^[A-Z]{3}\d{2}[A-Z]$"),   # ABC12D
}
EJEMPLO_PLACA = {"carro": "ABC123", "moto": "ABC12D"}


# ---------- utilidades ----------

def _limpiar(texto):
    return (texto or "").strip()


def _guardar():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ReglaNegocioError("No se pudo guardar: el dato ya existe o no es válido.")


def vehiculo_dentro(placa):
    return RegistroAcceso.query.filter_by(placa=placa, fecha_salida=None).first() is not None


def placas_dentro_de_usuario(usuario):
    registros = (RegistroAcceso.query
                 .join(Vehiculo, RegistroAcceso.placa == Vehiculo.placa)
                 .filter(Vehiculo.id_usuario == usuario.id,
                         RegistroAcceso.fecha_salida.is_(None))
                 .all())
    return [r.placa for r in registros]


# ---------- usuarios (RF-13 a RF-17) ----------

def obtener_usuario(id_usuario):
    usuario = db.session.get(Usuario, id_usuario)
    if not usuario:
        raise ReglaNegocioError("El usuario no existe.")
    return usuario


def listar_usuarios(busqueda=""):
    q = Usuario.query
    busqueda = _limpiar(busqueda)
    if busqueda:
        patron = f"%{busqueda}%"
        q = q.filter(or_(Usuario.nombre.ilike(patron),
                         Usuario.documento.ilike(patron)))
    return q.order_by(Usuario.nombre).all()


def _validar_usuario(nombre, documento, telefono):
    if not nombre:
        raise ReglaNegocioError("El nombre es obligatorio.")
    if not documento:
        raise ReglaNegocioError("El documento es obligatorio.")
    if len(nombre) > 100:
        raise ReglaNegocioError("El nombre no puede superar 100 caracteres.")
    if len(documento) > 20:
        raise ReglaNegocioError("El documento no puede superar 20 caracteres.")
    if len(telefono) > 20:
        raise ReglaNegocioError("El teléfono no puede superar 20 caracteres.")


def registrar_usuario(nombre, documento, telefono=""):
    nombre, documento, telefono = _limpiar(nombre), _limpiar(documento), _limpiar(telefono)
    _validar_usuario(nombre, documento, telefono)
    if Usuario.query.filter_by(documento=documento).first():
        raise ReglaNegocioError("El documento ya está registrado.")
    usuario = Usuario(nombre=nombre, documento=documento,
                      telefono=telefono or None, activo=True)
    db.session.add(usuario)
    _guardar()
    return usuario


def editar_usuario(id_usuario, nombre, documento, telefono=""):
    usuario = obtener_usuario(id_usuario)
    nombre, documento, telefono = _limpiar(nombre), _limpiar(documento), _limpiar(telefono)
    _validar_usuario(nombre, documento, telefono)
    otro = Usuario.query.filter(Usuario.documento == documento,
                                Usuario.id != usuario.id).first()
    if otro:
        raise ReglaNegocioError("El documento ya pertenece a otro usuario.")
    usuario.nombre = nombre
    usuario.documento = documento
    usuario.telefono = telefono or None
    _guardar()
    return usuario


def cambiar_estado_usuario(id_usuario):
    """Desactiva al usuario si está activo; lo reactiva si está inactivo."""
    usuario = obtener_usuario(id_usuario)
    if usuario.activo:
        dentro = placas_dentro_de_usuario(usuario)
        if dentro:
            raise ReglaNegocioError(
                "No se puede desactivar: el vehículo " + ", ".join(dentro)
                + " está dentro del parqueadero.")
        usuario.activo = False
    else:
        usuario.activo = True
    _guardar()
    return usuario


# ---------- vehículos (RF-18 a RF-22) ----------

def _validar_tipo(tipo):
    tipo = _limpiar(tipo).lower()
    if tipo not in TIPOS:
        raise ReglaNegocioError("El tipo debe ser carro o moto.")
    return tipo


def _validar_formato_placa(placa, tipo):
    if not PATRON_PLACA[tipo].match(placa):
        raise ReglaNegocioError(
            f"La placa no tiene un formato válido para {tipo} "
            f"(ejemplo: {EJEMPLO_PLACA[tipo]}).")


def _parsear_fecha(texto):
    try:
        return datetime.strptime(_limpiar(texto), "%Y-%m-%d").date()
    except ValueError:
        raise ReglaNegocioError("La fecha de vencimiento no es válida.")


def obtener_vehiculo(placa):
    vehiculo = db.session.get(Vehiculo, _limpiar(placa).upper())
    if not vehiculo:
        raise ReglaNegocioError("El vehículo no existe.")
    return vehiculo


def registrar_vehiculo(id_usuario, placa, tipo, vence):
    usuario = obtener_usuario(id_usuario)
    if not usuario.activo:
        raise ReglaNegocioError("El usuario está inactivo.")
    placa = _limpiar(placa).upper()
    if not placa:
        raise ReglaNegocioError("La placa es obligatoria.")
    tipo = _validar_tipo(tipo)
    _validar_formato_placa(placa, tipo)
    fecha = _parsear_fecha(vence)

    existente = db.session.get(Vehiculo, placa)
    if existente:
        if existente.activo:
            raise ReglaNegocioError("La placa ya está registrada.")
        raise ReglaNegocioError("La placa pertenece a un vehículo retirado.")

    vehiculo = Vehiculo(placa=placa, tipo=tipo, mensualidad_vence=fecha,
                        id_usuario=usuario.id, activo=True)
    db.session.add(vehiculo)
    _guardar()
    return vehiculo


def editar_vehiculo(placa, tipo, vence):
    vehiculo = obtener_vehiculo(placa)
    if not vehiculo.activo:
        raise ReglaNegocioError("El vehículo está retirado y no se puede editar.")
    tipo = _validar_tipo(tipo)
    if tipo != vehiculo.tipo and vehiculo_dentro(vehiculo.placa):
        raise ReglaNegocioError(
            "No se puede cambiar el tipo de un vehículo que está dentro del parqueadero.")
    _validar_formato_placa(vehiculo.placa, tipo)
    vehiculo.tipo = tipo
    vehiculo.mensualidad_vence = _parsear_fecha(vence)
    _guardar()
    return vehiculo


def retirar_vehiculo(placa):
    vehiculo = obtener_vehiculo(placa)
    if vehiculo_dentro(vehiculo.placa):
        raise ReglaNegocioError(
            "No se puede retirar un vehículo que está dentro del parqueadero.")
    vehiculo.activo = False
    _guardar()
    return vehiculo