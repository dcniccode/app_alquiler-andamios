from enum import UNIQUE

from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC, timedelta
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/alquiler_andamios'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(8), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_registro = db.Column(db.DateTime, default = datetime.now(UTC))
    fecha_entrega = db.Column(db.DateTime, default = datetime.now(UTC))
    telefono = db.Column(db.String(9), nullable=False)
    dias = db.Column(db.Integer, nullable=False)

    def calcular_fecha_entrega(self, dias):
        self.fecha_entrega = datetime.now(UTC) + timedelta(days = dias)

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'

class ClienteForm(FlaskForm):
    dni = StringField('DNI', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    dias = IntegerField('Días a alquilar', validators=[DataRequired()])
    submit = SubmitField('Registrar Cliente')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/registrar_cliente', methods=['GET', 'POST'])
def registrar_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            dni = form.dni.data,
            nombre = form.nombre.data,
            apellido = form.apellido.data,
            telefono = form.telefono.data,
            dias = form.dias.data
        )

        cliente.calcular_fecha_entrega(dias = form.dias.data)

        db.session.add(cliente)
        db.session.commit()
        return redirect(url_for('cliente_registrado'))

    return render_template('register.html', form=form)

@app.route('/cliente_registrado')
def cliente_registrado():
    flash('Cliente registrado exitosamente!')
    return redirect(url_for('index'))

@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if request.method == 'POST':
        return redirect(url_for('index'))
    else:
        listas_clientes = Cliente.query.order_by(Cliente.fecha_registro.asc()).all()
    return render_template('clientes.html', clientes=listas_clientes)

@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)

    # por si hay campos vacios esto evitara que se sobreescriban como cadenas vacias
    if request.method == 'POST':
        if request.form['dni']:
            cliente.dni = request.form['dni']
        if request.form['nombre']:
            cliente.nombre = request.form['nombre']
        if request.form['apellido']:
            cliente.apellido = request.form['apellido']
        if request.form['telefono']:
            cliente.telefono = request.form['telefono']
        if request.form['dias']:
            try:
                cliente.dias = int(request.form['dias'])  # Convertir 'dias' a entero
                cliente.calcular_fecha_entrega(dias=cliente.dias)
            except ValueError:
                # Si no es un número válido, puedes manejar el error
                print("El valor de 'dias' no es válido. Debe ser un número entero.")
        nueva_fecha = request.form.get('fecha_registro')
        if nueva_fecha:
            cliente.fecha_registro = datetime.strptime(nueva_fecha, '%Y-%m-%d')

        try:
            db.session.commit()
            return redirect(url_for('clientes'))
        except:
            return 'Hubo un error al actualizar los datos del cliente'
    else:
        return render_template('update.html', cliente=cliente)

@app.route('/eliminar_cliente/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)

    try:
        db.session.delete(cliente)
        db.session.commit()
        return redirect(url_for('clientes'))
    except:
        return 'Hubo un error al eliminar al cliente'

if __name__ == '__main__':
    app.run()
