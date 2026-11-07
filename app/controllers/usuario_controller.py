from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services import usuario_service as svc
from app.services.registro_service import ReglaNegocioError

bp = Blueprint("usuario", __name__)


# ---------- usuarios ----------

@bp.route("/usuarios")
def usuarios():
    q = request.args.get("q", "")
    return render_template("usuarios.html", usuarios=svc.listar_usuarios(q), q=q)


@bp.route("/usuarios/nuevo", methods=["GET", "POST"])
def usuario_nuevo():
    datos = {"nombre": "", "documento": "", "telefono": ""}
    if request.method == "POST":
        datos = {k: request.form.get(k, "") for k in datos}
        try:
            svc.registrar_usuario(**datos)
            flash("Usuario registrado correctamente.", "ok")
            return redirect(url_for("usuario.usuarios"))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("usuario_form.html", titulo="Nuevo usuario", datos=datos,
                           cancelar=url_for("usuario.usuarios"))


@bp.route("/usuarios/<int:id_usuario>")
def usuario_detalle(id_usuario):
    try:
        usuario = svc.obtener_usuario(id_usuario)
    except ReglaNegocioError as e:
        flash(str(e), "error")
        return redirect(url_for("usuario.usuarios"))
    return render_template("usuario_detalle.html", usuario=usuario)


@bp.route("/usuarios/<int:id_usuario>/editar", methods=["GET", "POST"])
def usuario_editar(id_usuario):
    try:
        usuario = svc.obtener_usuario(id_usuario)
    except ReglaNegocioError as e:
        flash(str(e), "error")
        return redirect(url_for("usuario.usuarios"))
    datos = {"nombre": usuario.nombre, "documento": usuario.documento,
             "telefono": usuario.telefono or ""}
    if request.method == "POST":
        datos = {k: request.form.get(k, "") for k in datos}
        try:
            svc.editar_usuario(id_usuario, **datos)
            flash("Usuario actualizado.", "ok")
            return redirect(url_for("usuario.usuario_detalle", id_usuario=id_usuario))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("usuario_form.html", titulo="Editar usuario", datos=datos,
                           cancelar=url_for("usuario.usuario_detalle", id_usuario=id_usuario))


@bp.route("/usuarios/<int:id_usuario>/estado", methods=["POST"])
def usuario_estado(id_usuario):
    try:
        usuario = svc.cambiar_estado_usuario(id_usuario)
        flash("Usuario activado." if usuario.activo else "Usuario desactivado.", "ok")
    except ReglaNegocioError as e:
        flash(str(e), "error")
    return redirect(url_for("usuario.usuario_detalle", id_usuario=id_usuario))


# ---------- vehículos ----------

@bp.route("/usuarios/<int:id_usuario>/vehiculos/nuevo", methods=["GET", "POST"])
def vehiculo_nuevo(id_usuario):
    try:
        usuario = svc.obtener_usuario(id_usuario)
    except ReglaNegocioError as e:
        flash(str(e), "error")
        return redirect(url_for("usuario.usuarios"))
    datos = {"placa": "", "tipo": "carro", "vence": ""}
    if request.method == "POST":
        datos = {k: request.form.get(k, "") for k in datos}
        try:
            svc.registrar_vehiculo(id_usuario, **datos)
            flash("Vehículo registrado correctamente.", "ok")
            return redirect(url_for("usuario.usuario_detalle", id_usuario=id_usuario))
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("vehiculo_form.html", titulo="Nuevo vehículo",
                           usuario=usuario, datos=datos, editando=False,
                           cancelar=url_for("usuario.usuario_detalle", id_usuario=id_usuario))


@bp.route("/vehiculos/<placa>/editar", methods=["GET", "POST"])
def vehiculo_editar(placa):
    try:
        vehiculo = svc.obtener_vehiculo(placa)
    except ReglaNegocioError as e:
        flash(str(e), "error")
        return redirect(url_for("usuario.usuarios"))
    detalle = url_for("usuario.usuario_detalle", id_usuario=vehiculo.id_usuario)
    datos = {"placa": vehiculo.placa, "tipo": vehiculo.tipo,
             "vence": vehiculo.mensualidad_vence.isoformat()}
    if request.method == "POST":
        datos["tipo"] = request.form.get("tipo", "")
        datos["vence"] = request.form.get("vence", "")
        try:
            svc.editar_vehiculo(vehiculo.placa, datos["tipo"], datos["vence"])
            flash("Vehículo actualizado.", "ok")
            return redirect(detalle)
        except ReglaNegocioError as e:
            flash(str(e), "error")
    return render_template("vehiculo_form.html", titulo="Editar vehículo",
                           usuario=vehiculo.usuario, datos=datos, editando=True,
                           cancelar=detalle)


@bp.route("/vehiculos/<placa>/retirar", methods=["POST"])
def vehiculo_retirar(placa):
    try:
        vehiculo = svc.retirar_vehiculo(placa)
        flash(f"Vehículo {vehiculo.placa} retirado.", "ok")
        return redirect(url_for("usuario.usuario_detalle", id_usuario=vehiculo.id_usuario))
    except ReglaNegocioError as e:
        flash(str(e), "error")
    return redirect(url_for("usuario.usuarios"))