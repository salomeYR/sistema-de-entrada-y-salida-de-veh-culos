from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Celda, RegistroAcceso
from app.services.registro_service import ReglaNegocioError

TIPOS = ("carro", "moto")


def _guardar():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ReglaNegocioError("No se pudo guardar: el código de celda ya existe.")


def estado_celda(celda):
    """Devuelve 'deshabilitada', 'ocupada' o 'libre'."""
    if not celda.activa:
        return "deshabilitada"
    if celda.ocupada:
        return "ocupada"
    return "libre"


def obtener_celda(id_celda):
    celda = db.session.get(Celda, id_celda)
    if not celda:
        raise ReglaNegocioError("La celda no existe.")
    return celda


def listar_celdas(tipo="", estado=""):
    q = Celda.query
    if tipo in TIPOS:
        q = q.filter(Celda.tipo == tipo)
    if estado == "libre":
        q = q.filter(Celda.activa.is_(True), Celda.ocupada.is_(False))
    elif estado == "ocupada":
        q = q.filter(Celda.activa.is_(True), Celda.ocupada.is_(True))
    elif estado == "deshabilitada":
        q = q.filter(Celda.activa.is_(False))
    return q.order_by(Celda.tipo, Celda.codigo).all()


def resumen():
    """Totales por tipo: total, libres, ocupadas y deshabilitadas (RF-29)."""
    clave = {"libre": "libres", "ocupada": "ocupadas", "deshabilitada": "deshabilitadas"}
    datos = {t: {"total": 0, "libres": 0, "ocupadas": 0, "deshabilitadas": 0}
             for t in TIPOS}
    for celda in Celda.query.all():
        fila = datos.get(celda.tipo)
        if fila is None:
            continue
        fila["total"] += 1
        fila[clave[estado_celda(celda)]] += 1
    return datos


def _validar(codigo, tipo):
    codigo = (codigo or "").strip().upper()
    tipo = (tipo or "").strip().lower()
    if not codigo:
        raise ReglaNegocioError("El código es obligatorio.")
    if len(codigo) > 10:
        raise ReglaNegocioError("El código no puede superar 10 caracteres.")
    if tipo not in TIPOS:
        raise ReglaNegocioError("El tipo debe ser carro o moto.")
    return codigo, tipo


def registrar_celda(codigo, tipo):
    codigo, tipo = _validar(codigo, tipo)
    if Celda.query.filter_by(codigo=codigo).first():
        raise ReglaNegocioError("El código de celda ya existe.")
    celda = Celda(codigo=codigo, tipo=tipo, ocupada=False, activa=True)
    db.session.add(celda)
    _guardar()
    return celda


def editar_celda(id_celda, codigo, tipo):
    celda = obtener_celda(id_celda)
    if celda.ocupada:
        raise ReglaNegocioError("No se puede editar una celda ocupada.")
    codigo, tipo = _validar(codigo, tipo)
    otra = Celda.query.filter(Celda.codigo == codigo, Celda.id != celda.id).first()
    if otra:
        raise ReglaNegocioError("El código de celda ya existe.")
    celda.codigo = codigo
    celda.tipo = tipo
    _guardar()
    return celda


def cambiar_estado_celda(id_celda):
    """Deshabilita la celda si está habilitada; la habilita si está deshabilitada."""
    celda = obtener_celda(id_celda)
    if celda.activa:
        if celda.ocupada:
            raise ReglaNegocioError("No se puede deshabilitar una celda ocupada.")
        celda.activa = False
    else:
        celda.activa = True
    _guardar()
    return celda


def eliminar_celda(id_celda):
    celda = obtener_celda(id_celda)
    if celda.ocupada:
        raise ReglaNegocioError("No se puede eliminar una celda ocupada.")
    if RegistroAcceso.query.filter_by(id_celda=celda.id).first():
        raise ReglaNegocioError(
            "La celda tiene historial de accesos; solo puede deshabilitarse.")
    db.session.delete(celda)
    db.session.commit()