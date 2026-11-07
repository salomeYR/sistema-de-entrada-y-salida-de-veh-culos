from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services import celda_service as svc
from app.services.registro_service import ReglaNegocioError

bp = Blueprint("celda", __name__)


@bp.route("/celdas")
def celdas():
    tipo = request.args.get("tipo", "")
    estado = request.args.get("estado", "")
    return render_template("celdas.html", celdas=svc.listar_celdas(tipo, estado),
                           resumen=svc.resumen(), tipo=tipo, estado=estado,
                           estado_de=svc.estado_celda)


@bp.route("/celdas/nueva", methods=["GET", "POST"])
def celda_nueva():
    datos = {"codigo": "", "tipo": "carro"}
    if request.method == "POST":
        datos = {k: request.form.get(k, "") for k in datos}
        try:
            svc.registrar_celda(**datos)
            flash("Celda registrada correctamente.", "ok")
            return redirect(url_for("celda.celdas"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("celda_form.html", titulo="Nueva celda", datos=datos)


@bp.route("/celdas/<int:id_celda>/editar", methods=["GET", "POST"])
def celda_editar(id_celda):
    try:
        celda = svc.obtener_celda(id_celda)
    except ReglaNegocioError as e:
        flash(str(e), "error")
        return redirect(url_for("celda.celdas"))
    datos = {"codigo": celda.codigo, "tipo": celda.tipo}
    if request.method == "POST":
        datos = {k: request.form.get(k, "") for k in datos}
        try:
            svc.editar_celda(id_celda, **datos)
            flash("Celda actualizada.", "ok")
            return redirect(url_for("celda.celdas"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("celda_form.html", titulo="Editar celda", datos=datos)


@bp.route("/celdas/<int:id_celda>/estado", methods=["POST"])
def celda_estado(id_celda):
    try:
        celda = svc.cambiar_estado_celda(id_celda)
        flash("Celda habilitada." if celda.activa else "Celda deshabilitada.", "ok")
    except ReglaNegocioError as e:
        flash(str(e), "error")
    return redirect(url_for("celda.celdas"))


@bp.route("/celdas/<int:id_celda>/eliminar", methods=["POST"])
def celda_eliminar(id_celda):
    try:
        svc.eliminar_celda(id_celda)
        flash("Celda eliminada.", "ok")
    except ReglaNegocioError as e:
        flash(str(e), "error")
    return redirect(url_for("celda.celdas"))
