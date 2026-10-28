from datetime import date, timedelta
from app import create_app, db
from app.models import Usuario, Vehiculo, Celda

app = create_app()

with app.app_context():
    if Usuario.query.first():
        print("Los datos de prueba ya existen.")
    else:
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
        print("Datos de prueba creados.")