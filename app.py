from flask import Flask, jsonify,request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'my_secret' #debo cambiar esto en produccion

# debajo de esta linea añado la configuracion del mailtrap para la app de flask
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
#app.config['MAIL_USERNAME'] = '67f079a594674f'
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USERNAME')
#app.config['MAIL_PASSWORD'] = '8e3aec4fba10ac'
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail= Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Base de Dato Creada!')


@app.cli.command('db_drop')    
def db_drop():
    db.drop_all()
    print('Base de datos eliminada!')


# En esta pate  vamos a definir los planetas
@app.cli.command('db_seed')
def db_seed():
    mercurio = Planet(planet_id='',
                      planet_name='Mercurio',
                      planet_type='Clase D',
                      home_star='Sol',
                      masa=3.258e23,
                      radius=1516,
                      distance=35.98e6)
    
    venus   = Planet(planet_name='Venus',
                      planet_type='Clase K',
                      home_star='Sol',
                      masa=4.867e24,
                      radius=3760,
                      distance=6724e6)
    
    tierra   = Planet(planet_name='Tierra',
                      planet_type='Clase M',
                      home_star='Sol',
                      masa=5.972e24,
                      radius=3959,
                      distance=92.96e6)
    
    db.session.add(mercurio)
    db.session.add(venus)
    db.session.add(tierra)

    tes_user = User(nombre='Elvin',
                    apellido='Cooper',
                    email='probandohoy@gmail.com',
                    password='password')
    
    db.session.add(tes_user)
    db.session.commit()
    print('Base de datos definida!')


@app.route('/')
def home():    
    return "<h1> Planets API for everyone ! </h1>"


@app.route('/super_simple')
def super_simple():
    return jsonify(message='Bienvenidos a la API planetaria !'), 200


@app.route('/not_found')
def not_found():
    return jsonify(message='The resource was not found',
                   titulo='Esto es un titulo'), 400

@app.route('/parameters')
def parameters():
    nombre = request.args.get('nombre')
    edad   = int(request.args.get('edad'))
    if edad < 18:
        return jsonify(message='Lo siento '+nombre +' eres menor de edad'), 401
    else:
        return jsonify(message='Ahora si '+nombre+' ya eres mayor de edad')
    

# Ahora haremos los mismo de arriba pero usando Variables URL
@app.route('/url_variables/<string:nombre>/<int:edad>')    # en esta parte definimos los parametros dentro de la ruta
def url_variables(nombre: str, edad: int): 
    if edad < 18:
        return jsonify(message='Lo siento '+nombre +' eres menor de edad'), 401
    else:
        return jsonify(message='Ahora si '+nombre+' ya eres mayor de edad')
    

@app.route('/planets', methods=['GET'])
def planets():
    planet_list = Planet.query.all()
    result = planets_schema.dump(planet_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(mensaje='Este email ya existe !'), 409
    else:
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        password = request.form['password']
        user= User(nombre=nombre, apellido=apellido, email=email, password=password)
        db.session.commit()
        return jsonify(mensaje="Usuario creado satisfactoriamente"), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password= request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()   
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Inicio de sesion exitoso', access_token=access_token)
    else:
        return jsonify(message='email o contraseña incorrectos'), 401
    

@app.route('/retrieve_password/<string:email>', methods=['GET'])        
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Tu contraseña para el planets API es '+ user.password,
                      sender='adminplanetsAPI@gmail.com',
                      recipients=[email])
        mail.send(msg)
        return jsonify(mensaje='La contraseña enviada a ' + email)
    else:
        return jsonify(mensaje='Esta dirrecion de email no existe')    


@app.route('/planet_details/<int:planet_id>', methods=['GET'])        
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result), 200
    else:
        return jsonify(mensaje='Este planeta no existe'),404
    

@app.route('/add_planet', methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(mensaje='Este planeta ya existe !'), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        masa = float(request.form['masa'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = Planet(planet_name = planet_name,
                            home_star = home_star,
                            masa = masa,
                            radius = radius,
                            distance = distance)
        
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(mensaje="Usted ha añadido un nuevo planeta !"),200


@app.route('/update_planet', methods=['PUT'])
@jwt_required()
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star   = request.form['home_star']
        planet.masa  = float(request.form['masa'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(mensaje='Usted ha actualizado un planeta'), 202
    else:
        jsonify(mensaje='Este planeta no existe en la base de datos'), 404


@app.route('/delete_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(mensaje='EL planeta ha sido eliminado !'), 202
    else:
        return jsonify(mensaje='Este planeta no existe !'), 404

# En esta parte vamos a crear los modelo s de BD de SQLAlchemy
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    apellido = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
   __tablename__ = 'planets'
   planet_id = Column(Integer, primary_key=True)
   planet_name = Column(String)
   planet_type = Column(String)
   home_star = Column(String)
   masa = Column(Float)
   radius = Column(Float)
   distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'nombre', 'apellido', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'masa', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':  
   app.run(debug=True)