from datetime import date, timedelta
 
import pytest
 
from app import create_app, db
from app.models import Usuario, Vehiculo, Celda, RegistroAcceso
from app.services import celda_service, registro_service
 
 
@pytest.fixture
def app(tmp_path):
    ruta = (tmp_path / "prueba.db").as_posix()
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta}"})
    with app.app_context():
        # Mismos datos que seed.py
        u1 = Usuario(nombre="Carlos Pérez", documento="1001", telefono="3001112233")
        u2 = Usuario(nombre="Ana Gómez", documento="1002", telefono="3004445566")
        db.session.add_all([u1, u2])
        db.session.flush()
        hoy = date.today()
        db.session.add_all([
            Vehiculo(placa="ABC123", tipo="carro", mensualidad_vence=hoy + timedelta(days=30), id_usuario=u1.id),
            Vehiculo(placa="XYZ98A", tipo="moto", mensualidad_vence=hoy + timedelta(days=15), id_usuario=u2.id),
            Vehiculo(placa="VEN000", tipo="carro", mensualidad_vence=hoy - timedelta(days=5), id_usuario=u2.id),
        ])
        db.session.add_all([Celda(codigo=f"C-{i}", tipo="carro") for i in range(1, 6)] +
                           [Celda(codigo=f"M-{i}", tipo="moto") for i in range(1, 4)])
        db.session.commit()
        yield app
        db.session.remove()
        db.engine.dispose()
 
 
@pytest.fixture
def client(app):
    return app.test_client()
 
 
def post(client, url, **datos):
    r = client.post(url, data=datos, follow_redirects=True)
    assert r.status_code == 200
    return r.get_data(as_text=True)
 
 
def get(client, url):
    r = client.get(url)
    assert r.status_code == 200
    return r.get_data(as_text=True)
 
 
def futuro(dias=30):
    return str(date.today() + timedelta(days=dias))
 
 
def celda_id(codigo):
    return Celda.query.filter_by(codigo=codigo).first().id
 
 
# ------------------------- Usuarios y vehículos -------------------------
 
def test_PU_01_registrar_usuario_valido(client):
    html = post(client, "/usuarios/nuevo", nombre="Luis Mora", documento="1003", telefono="3007778899")
    assert "Usuario registrado correctamente" in html
    assert "Luis Mora" in get(client, "/usuarios")
 
 
def test_PU_02_documento_duplicado(client):
    html = post(client, "/usuarios/nuevo", nombre="Otro", documento="1001", telefono="")
    assert "El documento ya está registrado" in html
    assert Usuario.query.count() == 2
 
 
def test_PU_03_nombre_vacio(client):
    html = post(client, "/usuarios/nuevo", nombre="", documento="1005", telefono="")
    assert "El nombre es obligatorio" in html
    assert Usuario.query.count() == 2
 
 
def test_PU_04_buscar_por_nombre(client):
    html = get(client, "/usuarios?q=Ana")
    assert "Ana Gómez" in html
    assert "Carlos Pérez" not in html
 
 
def test_PU_05_busqueda_sin_coincidencias(client):
    assert "Sin resultados" in get(client, "/usuarios?q=zzz")
 
 
def test_PU_06_editar_telefono(client):
    html = post(client, "/usuarios/1/editar", nombre="Carlos Pérez", documento="1001", telefono="3119998877")
    assert "Usuario actualizado" in html
    assert db.session.get(Usuario, 1).telefono == "3119998877"
 
 
def test_PU_07_documento_de_otro_usuario(client):
    html = post(client, "/usuarios/1/editar", nombre="Carlos Pérez", documento="1002", telefono="")
    assert "ya pertenece a otro usuario" in html
    assert db.session.get(Usuario, 1).documento == "1001"
 
 
def test_PU_08_desactivar_usuario_sin_vehiculos_dentro(client):
    html = post(client, "/usuarios/1/estado")
    assert "Usuario desactivado" in html
    assert db.session.get(Usuario, 1).activo is False
    html = post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    assert "El usuario está inactivo" in html
 
 
def test_PU_09_desactivar_con_vehiculo_dentro(client):
    post(client, "/entrada", placa="XYZ98A", id_celda=str(celda_id("M-1")))
    html = post(client, "/usuarios/2/estado")
    assert "XYZ98A" in html and "dentro del parqueadero" in html
    assert db.session.get(Usuario, 2).activo is True
 
 
def test_PU_10_registrar_vehiculo_valido(client):
    html = post(client, "/usuarios/1/vehiculos/nuevo", placa="def456", tipo="carro", vence=futuro())
    assert "Vehículo registrado correctamente" in html
    v = db.session.get(Vehiculo, "DEF456")
    assert v is not None and v.id_usuario == 1
 
 
def test_PU_11_placa_duplicada(client):
    html = post(client, "/usuarios/1/vehiculos/nuevo", placa="ABC123", tipo="carro", vence=futuro())
    assert "La placa ya está registrada" in html
    assert Vehiculo.query.filter_by(placa="ABC123").count() == 1
 
 
def test_PU_12_formato_de_placa_invalido(client):
    html = post(client, "/usuarios/1/vehiculos/nuevo", placa="12", tipo="carro", vence=futuro())
    assert "formato válido" in html
    assert db.session.get(Vehiculo, "12") is None
 
 
def test_PU_13_renovar_vencimiento_permite_ingresar(client):
    assert "mensualidad del vehículo está vencida" in post(client, "/entrada", placa="VEN000", id_celda=str(celda_id("C-1")))
    html = post(client, "/vehiculos/VEN000/editar", tipo="carro", vence=futuro())
    assert "Vehículo actualizado" in html
    assert "Entrada registrada correctamente" in post(client, "/entrada", placa="VEN000", id_celda=str(celda_id("C-1")))
 
 
def test_PU_14_retirar_vehiculo_conserva_historial(client):
    post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    post(client, "/salida", placa="ABC123")
    html = post(client, "/vehiculos/ABC123/retirar")
    assert "retirado" in html
    assert db.session.get(Vehiculo, "ABC123").activo is False
    assert RegistroAcceso.query.filter_by(placa="ABC123").count() == 1
 
 
# ------------------------------- Celdas -------------------------------
 
def test_PC_01_registrar_celda_valida(client):
    html = post(client, "/celdas/nueva", codigo="c-6", tipo="carro")
    assert "Celda registrada correctamente" in html
    c = Celda.query.filter_by(codigo="C-6").first()
    assert c.ocupada is False and c.activa is True
 
 
def test_PC_02_codigo_duplicado(client):
    html = post(client, "/celdas/nueva", codigo="C-1", tipo="carro")
    assert "El código de celda ya existe" in html
    assert Celda.query.filter_by(codigo="C-1").count() == 1
 
 
def test_PC_03_tipo_invalido(client):
    html = post(client, "/celdas/nueva", codigo="C-7", tipo="")
    assert "carro o moto" in html
    assert Celda.query.filter_by(codigo="C-7").first() is None
 
 
def test_PC_04_filtrar_por_tipo_y_estado(client):
    html = get(client, "/celdas?tipo=moto&estado=libre")
    for codigo in ("M-1", "M-2", "M-3"):
        assert f"<td>{codigo}</td>" in html
    assert "<td>C-1</td>" not in html
 
 
def test_PC_05_resumen_de_ocupacion(client):
    post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    post(client, "/entrada", placa="XYZ98A", id_celda=str(celda_id("M-1")))
    r = celda_service.resumen()
    assert r["carro"] == {"total": 5, "libres": 4, "ocupadas": 1, "deshabilitadas": 0}
    assert r["moto"] == {"total": 3, "libres": 2, "ocupadas": 1, "deshabilitadas": 0}
    get(client, "/celdas")
 
 
def test_PC_06_editar_celda_libre(client):
    html = post(client, "/celdas/5/editar", codigo="C-9", tipo="carro")
    assert "Celda actualizada" in html
    assert db.session.get(Celda, 5).codigo == "C-9"
 
 
def test_PC_07_editar_celda_ocupada(client):
    post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    html = post(client, f"/celdas/{celda_id('C-1')}/editar", codigo="C-99", tipo="carro")
    assert "No se puede editar una celda ocupada" in html
    assert Celda.query.filter_by(codigo="C-1").first() is not None
 
 
def test_PC_08_deshabilitar_celda_libre(client):
    html = post(client, "/celdas/4/estado")
    assert "Celda deshabilitada" in html
    assert "C-4" not in [c.codigo for c in registro_service.celdas_libres()]
    assert ">C-4 (carro)<" not in get(client, "/entrada")
 
 
def test_PC_09_deshabilitar_celda_ocupada(client):
    post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    html = post(client, f"/celdas/{celda_id('C-1')}/estado")
    assert "No se puede deshabilitar una celda ocupada" in html
    assert Celda.query.filter_by(codigo="C-1").first().activa is True
 
 
def test_PC_10_habilitar_celda(client):
    post(client, "/celdas/4/estado")
    html = post(client, "/celdas/4/estado")
    assert "Celda habilitada" in html
    assert "C-4" in [c.codigo for c in registro_service.celdas_libres()]
 
 
def test_PC_11_eliminar_celda_sin_historial(client):
    post(client, "/celdas/nueva", codigo="C-6", tipo="carro")
    html = post(client, f"/celdas/{celda_id('C-6')}/eliminar")
    assert "Celda eliminada" in html
    assert Celda.query.filter_by(codigo="C-6").first() is None
 
 
def test_PC_12_eliminar_celda_con_historial(client):
    post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    post(client, "/salida", placa="ABC123")
    html = post(client, f"/celdas/{celda_id('C-1')}/eliminar")
    assert "historial de accesos" in html
    assert Celda.query.filter_by(codigo="C-1").first() is not None
 
 
# ----------------- Regresión de la iteración 1 -----------------
 
def test_PR_01_entrada_con_celda_deshabilitada(client):
    post(client, "/celdas/4/estado")
    html = post(client, "/entrada", placa="ABC123", id_celda="4")
    assert "La celda está deshabilitada" in html
 
 
def test_PR_02_entrada_de_usuario_inactivo(client):
    post(client, "/usuarios/2/estado")
    html = post(client, "/entrada", placa="XYZ98A", id_celda=str(celda_id("M-1")))
    assert "El usuario está inactivo" in html
 
 
def test_PR_03_entrada_normal_sigue_funcionando(client):
    html = post(client, "/entrada", placa="ABC123", id_celda=str(celda_id("C-1")))
    assert "Entrada registrada correctamente" in html
    assert Celda.query.filter_by(codigo="C-1").first().ocupada is True
 
 
# ------- Correcciones de errores de la iteración 1 (extra) -------
 
def test_E_01_entrada_sin_celda_no_rompe(client):
    html = post(client, "/entrada", placa="ABC123", id_celda="")
    assert "seleccionar una celda válida" in html
 
 
def test_E_02_historial_con_fecha_invalida_no_rompe(client):
    assert "La fecha no es válida" in get(client, "/historial?fecha=hola")