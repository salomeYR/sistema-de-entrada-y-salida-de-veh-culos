from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services import registro_service as svc
from app.services.registro_service import ReglaNegocioError

bp = Blueprint("registro", __name__)


@bp.route("/")
def index():
    return render_template("index.html", dentro=len(svc.vehiculos_dentro()),
                           libres=len(svc.celdas_libres()))


@bp.route("/entrada", methods=["GET", "POST"])
def entrada():
    if request.method == "POST":
        try:
            id_celda = int(request.form.get("id_celda", ""))
            svc.registrar_entrada(request.form.get("placa", ""), id_celda)
            flash("Entrada registrada correctamente.", "ok")
            return redirect(url_for("registro.dentro"))
        except ValueError:
            flash("Debes seleccionar una celda válida.", "error")
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("entrada.html", celdas=svc.celdas_libres())


@bp.route("/salida", methods=["GET", "POST"])
def salida():
    if request.method == "POST":
        try:
            r = svc.registrar_salida(request.form.get("placa", ""))
            flash(f"Salida registrada. Celda {r.celda.codigo} liberada.", "ok")
            return redirect(url_for("registro.dentro"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("salida.html")


@bp.route("/dentro")
def dentro():
    return render_template("dentro.html", registros=svc.vehiculos_dentro())


@bp.route("/novedad", methods=["GET", "POST"])
def novedad():
    if request.method == "POST":
        try:
            svc.registrar_novedad(request.form.get("placa", ""),
                                  request.form.get("descripcion", ""))
            flash("Novedad registrada.", "ok")
            return redirect(url_for("registro.novedad"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("novedad.html", novedades=svc.novedades())


@bp.route("/historial")
def historial():
    placa = request.args.get("placa", "")
    fecha = request.args.get("fecha", "")
    try:
        registros = svc.historial(placa, fecha)
    except ReglaNegocioError as e:
        flash(str(e), "error")
        registros = []
    return render_template("historial.html", registros=registros,
                           placa=placa, fecha=fecha)
