from enum import UNIQUE
from numbers import Number

from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC, timedelta
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.fields.numeric import FloatField
from wtforms.validators import DataRequired, NumberRange

import os
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_size": 10,  # Máximo de conexiones abiertas
    "pool_recycle": 1800,  # Recicla conexiones cada 30 minutos
    "pool_pre_ping": True  # Verifica que la conexión siga activa
}

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
    monto = db.Column(db.Float, nullable=False, default=0.0)

    def calcular_fecha_entrega(self):
        if not self.fecha_registro:
            self.fecha_registro = datetime.now(UTC)  # Asegurar que tenga un valor
        self.fecha_entrega = self.fecha_registro + timedelta(days=self.dias)

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'

class ClienteForm(FlaskForm):
    dni = StringField('DNI', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    dias = IntegerField('Días a alquilar', validators=[DataRequired()])
    monto = FloatField('Monto', validators=[DataRequired(), NumberRange(min=0, message='El monto debe ser positivo')])
    submit = SubmitField('Registrar Cliente')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/registrar_cliente', methods=['GET', 'POST'])
def registrar_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            dni=form.dni.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            telefono=form.telefono.data,
            dias=form.dias.data if form.dias.data else 1,  # Evitar None
            monto=form.monto.data
        )

        cliente.calcular_fecha_entrega()

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
        search_term = request.form.get('search', '').strip()
        if search_term:
            lista_clientes = Cliente.query.filter(
                (Cliente.dni.ilike(f"%{search_term}%")) |
                (Cliente.nombre.ilike(f"%{search_term}%")) |
                (Cliente.apellido.ilike(f"%{search_term}%")) |
                (Cliente.telefono.ilike(f"%{search_term}%"))
            ).all()
        else:
            lista_clientes = Cliente.query.all()
    else:
        lista_clientes = Cliente.query.order_by(Cliente.fecha_registro.asc()).all()
    return render_template('clientes.html', clientes=lista_clientes)


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

        if request.form.get('fecha_registro'):
            cliente.fecha_registro = datetime.strptime(request.form['fecha_registro'], '%Y-%m-%d')

        if request.form.get('dias'):
            try:
                cliente.dias = int(request.form['dias'])
                cliente.calcular_fecha_entrega()
            except ValueError:
                print("El valor de 'dias' no es válido. Debe ser un número entero.")

        if cliente.fecha_registro or cliente.dias:
            cliente.calcular_fecha_entrega()

        if request.form.get('monto'):
            try:
                cliente.monto = float(request.form['monto'])
            except ValueError:
                return 'El valor del monto es inválido'

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
