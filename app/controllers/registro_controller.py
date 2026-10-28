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
            svc.registrar_entrada(request.form["placa"], int(request.form["id_celda"]))
            flash("Entrada registrada correctamente.", "ok")
            return redirect(url_for("registro.dentro"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("entrada.html", celdas=svc.celdas_libres())


@bp.route("/salida", methods=["GET", "POST"])
def salida():
    if request.method == "POST":
        try:
            r = svc.registrar_salida(request.form["placa"])
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
            svc.registrar_novedad(request.form["placa"], request.form["descripcion"])
            flash("Novedad registrada.", "ok")
            return redirect(url_for("registro.novedad"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("novedad.html", novedades=svc.novedades())


@bp.route("/historial")
def historial():
    placa = request.args.get("placa", "")
    fecha = request.args.get("fecha", "")
    return render_template("historial.html", registros=svc.historial(placa, fecha),
                           placa=placa, fecha=fecha)