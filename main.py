from flask import Flask, render_template, request, make_response, session,escape,redirect,url_for,flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import  Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import text
from sqlalchemy.dialects import mysql
from flask_marshmallow import Marshmallow
from flask import json
from sqlalchemy.ext.declarative import declarative_base
import json
Base = declarative_base()


import requests
import sqlite3
import os


#----- Base de datos (Tablas) -----

dbdir = "sqlite:///" + os.path.abspath(os.getcwd()) + "/database.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

#Tabla para guardar las dos llaves primarias.
association_table = db.Table('association_table',
                          db.Column('correo_estudiante',Integer,ForeignKey('estudiante.correo_estudiante')),
                          db.Column('vivienda_id',Integer,ForeignKey('vivienda.codigo_Vivienda')),
                          db.Column('estado',db.String(80))
                          )


association_table2 = db.Table('association_table2',
                          db.Column('correo_dueño',Integer,ForeignKey('dueño.correo_dueño')),
                          db.Column('vivienda_id',Integer,ForeignKey('vivienda.codigo_Vivienda'))
                          )


class Estudiante(db.Model):
    __tablename__ = 'estudiante'
    correo_estudiante = db.Column(db.String(80), primary_key = True)
    username = db.Column(db.String(80),nullable = True)
    password = db.Column(db.String(80),nullable =True)
    pais = db.Column(db.String(80),nullable = True)
    genero = db.Column(db.String(20),nullable = True)
    edad = db.Column(mysql.BIGINT,nullable=True)
    idioma = db.Column(db.String(20),nullable = True)
    contacto =  db.Column(mysql.BIGINT,nullable = True) 

    viviendasN = relationship("Vivienda",secondary="solicitud") 
    viviendas = db.relationship("Vivienda",secondary=association_table)


class Vivienda(db.Model):
    __tablename__ = 'vivienda'
    codigo_Vivienda = db.Column(db.Integer, primary_key = True)
    latitud = db.Column(db.String(80),nullable =True)
    longitud = db.Column(db.String(80),nullable =True)
    dueño = db.Column(db.String(80),nullable=True)
    descripcion = db.Column(db.String(120),nullable=True)
    tipo = db.Column(db.String(2),nullable=True)
    reglas = db.Column(db.String(120),nullable=True)


    estudiantesN = relationship("Estudiante",secondary="solicitud") 
    estudiantes = db.relationship("Estudiante",secondary=association_table)
    dueñox = db.relationship("Dueño",secondary=association_table2)


class Dueño(db.Model):
    __tablename__ = 'dueño'
    correo_dueño = db.Column(db.String(80), primary_key = True)
    username = db.Column(db.String(80),nullable = True)
    password = db.Column(db.String(80),nullable =True)


    viviendas = db.relationship("Vivienda",secondary=association_table2)


class Solicitud(db.Model):
    __tablename__="solicitud"
    codigo_Solicitud =  db.Column(db.Integer, primary_key=True)
    estudiante_correo = db.Column(Integer, ForeignKey('estudiante.correo_estudiante'))
    vivienda_codigo = db.Column(Integer, ForeignKey('vivienda.codigo_Vivienda'))
    estado = db.Column(db.String(80),nullable = True)

    estudiante = relationship("Estudiante", backref=backref("vivienda_assoc"))
    vivienda = relationship("Vivienda", backref=backref("estudiante_assoc"))




















#----- Todos los / -----

# Inicio del programa
@app.route("/",methods=['GET','POST'])
def inicio():
    estu = Estudiante.query.all()
    due = Dueño.query.all()
    tipo = "Logueate"

    for i in session:
        for k in due:
            if session[i] == k.correo_dueño:
                tipo = "Agregar vivienda"
                print(tipo)
                print("El perfil actual es de: " + session[i])
        
    for i in session:
        for k in estu:
            if session[i] == k.correo_estudiante:
                tipo = "Ver viviendas"
                print(tipo)
                print("El perfil actual es de: " + session[i])
        
    return render_template("base.html",tipo = tipo)


#----- Mapa para los dueños -----
@app.route("/mapa",methods=['GET','POST'])
def mapa():
    if request.method == 'POST':
        #Guarda la vivienda del dueño
        y = request.form['latitud']
        x = request.form['longitud']
        print(y)
        print(x)
        c = Dueño.query.filter_by(correo_dueño = session["correo_dueño"]).first()
        new_vivienda = Vivienda(latitud = request.form['latitud'],longitud = request.form['longitud'],dueño = c.username,descripcion = request.form["descripcion"],reglas = request.form["reglas"])
        db.session.add(new_vivienda)
        db.session.commit()
        #Guardar a la tabla association_table2 
        s = Vivienda.query.filter_by(latitud = request.form['latitud']).first()
        print(s)
        c.viviendas.append(s)
        db.session.add(c)
        db.session.commit()
        return '200'
        
    return render_template("mapa_viviendas.html")




#----- Mapa para el estudiante -----
@app.route("/mapaEstudiante",methods=['GET','POST'])
def mapaEstudiante():
    if request.method == 'POST':
        #Aca recibo el código de la vivienda
        nose = request.form['xd']
        print("El dueño es: " + nose)

        #Agrego a la tabla Solicitud
        x = Solicitud.query.all()
        #Hago el código de la solicitud
        codigo_SolicitudNew = None
        for u in x:
            codigo_SolicitudNew = u.codigo_Solicitud
        else:
            if codigo_SolicitudNew == None:
                codigo_SolicitudNew = 1
        print(codigo_SolicitudNew+1)
        #Guardo en la tabla solicitud
        i = Estudiante.query.filter_by(correo_estudiante = session["correo_estudiante"]).first()
        j = Vivienda.query.filter_by(codigo_Vivienda = nose).first()
        ij = Solicitud(estudiante = i,vivienda = j,estado ="Pendiente",codigo_Solicitud = codigo_SolicitudNew+1)
        db.session.add(ij)
        db.session.commit()

        render_template("base.html")
        return '200'   

    #Envio la información de la viviendas para mostrarlas en el mapa
    g = Vivienda.query.all()
    ubicaciones = []
    for i in g:
        for o in i.dueñox:
            print(o.correo_dueño)
            n = o.correo_dueño
        ubicaciones.append({"Num":i.codigo_Vivienda,"Latitud":i.latitud,"Longitud":i.longitud,"Dueño":i.dueño,"Descripcion":i.descripcion,"Reglas":i.reglas,"Correo":n})
        
    print(type(ubicaciones))

    return render_template("mapa_estudiante.html",ubi = ubicaciones)


#----- Registro del estudiante: -----
@app.route("/registroEstudiante",methods=['GET','POST'])
def registro_estudiante():
    if request.method == 'POST':
        hashed_pw=generate_password_hash(request.form["password"],method="sha256")
        new_estudiante = Estudiante(correo_estudiante = request.form["correo"],username = request.form["username"],password = hashed_pw,pais = request.form["pais"],genero = request.form["genero"],edad = request.form["edad"],idioma = request.form["idioma"],contacto=request.form["numero"])
        db.session.add(new_estudiante)
        db.session.commit()
        return redirect("/login")
    return render_template("registro_estudiante.html")


#----- Registro dueño: ----- 
@app.route("/registroDueño",methods=['GET','POST'])
def registro_dueño():
    if request.method == 'POST':
        hashed_pw=generate_password_hash(request.form["password"],method="sha256")
        new_dueño = Dueño(correo_dueño = request.form["correo"],username = request.form["username"],password = hashed_pw)
        db.session.add(new_dueño)
        db.session.commit()
        return redirect("/login")
    return render_template("registro_dueño.html")


#----- Login -----
@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == "POST":
    
        estudiante = Estudiante.query.filter_by(correo_estudiante=request.form["correo"]).first()
        dueño = Dueño.query.filter_by(correo_dueño = request.form["correo"]).first()
        #Login para estudiante
        if estudiante and check_password_hash(estudiante.password, request.form["password"]):

            print("Se ha logeado")
            session["correo_estudiante"] = estudiante.correo_estudiante
            session.pop("correo_dueño",None)
            print("La session del dueño fue cerrada")
            print(session["correo_estudiante"])
            return redirect("/")
        else:
            #Login para dueño
            if dueño and check_password_hash(dueño.password,request.form["password"]):

                print("Se ha logeado")
                session["correo_dueño"] = dueño.correo_dueño
                session.pop("correo_estudiante",None)
                print("La session del estudiante fue cerrada")
                print(session["correo_dueño"])
                return redirect("/")

    return render_template("login.html")


#----- Ver el perfil del estudiante -----
@app.route("/perfilEstudiante",methods=['GET','POST'])
def perfilEstudiante():
    x = Estudiante.query.filter_by(correo_estudiante=session["correo_estudiante"]).first()
    print(x)
    #----- Mostrar las solicitudes aceptadas FALTA-----
   
    return render_template("perfil_estudiante.html",h = x)


#----- Ver el perfil del dueño -----
@app.route("/perfilDueño",methods=['GET','POST'])
def perfilDueño():
    y = Dueño.query.filter_by(correo_dueño = session["correo_dueño"]).first()
    print(y)
    #----- Mostrar cuales estudiantes estan en cada vivienda FALTA -----

    return render_template("perfil_dueno.html",h = y)


#----- Cerrar sesion -----
@app.route("/logout",methods=['GET','POST'])
def logout():
    if request.method == 'POST':
        session.pop("correo_estudiante",None)
        session.pop("correo_dueño",None)

    return redirect("/")


#----- Notificaciones dueño -----
@app.route("/notificacionesDueño",methods=['GET','POST'])
def notificacionesDueño():

    if request.method == 'POST':

        print("Aqui se agrega a association_table, sabiendo el código de la solicitud. FALTA")
        print(request.form['id'])
        #Necesito saber el código de la Solicitud
        #s = Vivienda.query.filter_by(codigo_Vivienda = 1).first()
        #print(s)
        #c = Estudiante.query.filter_by(correo_estudiante = session["correo_estudiante"]).first()
        #c.viviendas.append(s)
        #db.session.add(c)
        #db.session.commit()
        
        return '200'


    #----- Mostrar las solicitudes pendientes -----
    x = Solicitud.query.all()
    solicitudes = []
    
    for i in x:
        solicitudes.append({"Estudiante":i.estudiante,"Vivienda":i.vivienda,"estado":i.estado,"codigo_Solicitud":i.codigo_Solicitud})
        

    return render_template("notificaciones_dueños.html",solicitudes = solicitudes,dueño_actual = session["correo_dueño"])


#----- Notificaciones estudiante -----
@app.route("/notificacionesEstudiante",methods=['GET','POST'])
def notificacionesEstudiante():

    #----- Mostrar las solicitudes pendientes y rechazadas FALTA -----



    return render_template("notificaciones_estudiante.html")












@app.route("/probar",methods=['GET','POST'])
def probar():
    it = Estudiante.query.filter_by(correo_estudiante = session["correo_estudiante"]).first()
    john =  Vivienda.query.filter_by(codigo_Vivienda = 1).first()
    John_working_part_time_at_IT = Solicitud(estudiante = it,vivienda = john,estado ="PLsss")
    db.session.add(John_working_part_time_at_IT)
    db.session.commit()
    return "REVISA LA CONSOLA"


@app.route("/probarNose",methods=['GET','POST'])
def probarNose():

    x = Solicitud.query.all()
    print(x)
    
    for i in x:
        print(i.estudiante.contacto)
        print(i.estado)
        i.estado = "Pendiente"
        db.session.commit()
        print(i.estado)
        print(i.vivienda.dueño)
        print(i.vivienda.reglas)

    return "REVISA LA CONSOLA"




























#----- REDIRECCIONES -----

#----- Ir a inicio----- 
@app.route("/volverInicio",methods=["GET","POST"])
def volverInicio():
    if request.method == "POST":
        return redirect("/")


#----- Ir al mapa del dueño----- 
@app.route("/volverMapaD",methods=["GET","POST"])
def volverMapaD():
    if request.method == "POST":
        return redirect("/mapa")


#----- Ir al mapa del estudiante----- 
@app.route("/volverMapaE",methods=["GET","POST"])
def volverMapaE():
    if request.method == "POST":
        return redirect("/mapaEstudiante")


#----- Ir al registro del estudiante ----- 
@app.route("/irRegistroEstudiante",methods=["GET","POST"])
def irRegistroEstudiante():
    if request.method == "POST":
        return redirect("/registroEstudiante")


#----- Ir al registro del dueño -----
@app.route("/irRegistroDueño",methods=["GET","POST"])
def irRegistroDueño():
    if request.method == "POST":
        return redirect("/registroDueño")


#----- Ir al login ----
@app.route("/irLogin",methods=["GET","POST"])
def irLogin():
    if request.method == "POST":
        return redirect("/login")


#----- Ir al perfil del estudiante ----
@app.route("/irPerfilEstudiante",methods=["GET","POST"])
def irPerfilEstudiante():
    if request.method == "POST":
        return redirect("/perfilEstudiante")


#----- Ir al perfil del dueño ----
@app.route("/irPerfilDueño",methods=["GET","POST"])
def irPerfilDueño():
    if request.method == "POST":
        return redirect("/perfilDueño")


#----- Ir a las notificaciones del dueño ----
@app.route("/irNotificacionesDueño",methods=["GET","POST"])
def irNotificacionesDueño():
    if request.method == "POST":
        return redirect("/notificacionesDueño")


#----- Ir a las notificaciones del estudiante ----
@app.route("/irNotificacionesEstudiante",methods=["GET","POST"])
def irNotificacionesEstudiante():
    if request.method == "POST":
        return redirect("/notificacionesEstudiante")















app.secret_key = "12345"

if __name__=="__main__":
    db.create_all()
    app.run(debug=True)