from flask import Flask, render_template, request, make_response, session,escape,redirect,url_for,flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import  Table, Column, Integer, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import text
from sqlalchemy.dialects import mysql
from flask_marshmallow import Marshmallow
from flask import json
import json

import requests
import sqlite3
import os


#----- Base de datos (Conectar) -----

dbdir = "sqlite:///" + os.path.abspath(os.getcwd()) + "/database.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

#----- Base de datos (Tablas) -----

#Tabla para guardar las dos llaves primarias.
historial = db.Table('historial',
                          db.Column('correo_estudiante',Integer,ForeignKey('estudiante.correo_estudiante')),
                          db.Column('vivienda_id',Integer,ForeignKey('vivienda.codigo_Vivienda'))
                          )


asistencia_evento = db.Table('asistencia_evento',
                          db.Column('correo_estudiante',Integer,ForeignKey('estudiante.correo_estudiante')),
                          db.Column('codigo_evento',Integer,ForeignKey('evento.codigo_evento'))
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


    estudianteN = relationship("Vivienda",secondary= "solicitud") 
    estudianteE = relationship("Evento",secondary= asistencia_evento) 
    viviendas = db.relationship("Vivienda",secondary= historial)
    evento = db.relationship("Evento",back_populates= "estudiante_dueño")


class Vivienda(db.Model):
    __tablename__ = 'vivienda'
    codigo_Vivienda = db.Column(db.Integer, primary_key = True)
    latitud = db.Column(db.String(80),nullable =True)
    longitud = db.Column(db.String(80),nullable =True)
    direccion_exacta = db.Column(db.String(80),nullable =True)
    descripcion = db.Column(db.String(120),nullable=True)
    reglas = db.Column(db.String(120),nullable=True)
    precio = db.Column(db.String(120),nullable=True)
    tipo = db.Column(db.String(1),nullable=True)
    metodo_pago = db.Column(db.String(120),nullable=True)
    estado = db.Column(db.String(1),nullable=True)
    dueño_correo = db.Column(db.Integer,ForeignKey('dueño.correo_dueño'))


    dueño = db.relationship("Dueño",back_populates="viviendasU")
    estudiantes = db.relationship("Estudiante",secondary=historial)
    dueñosN = relationship("Estudiante",secondary="solicitud")
    

class Dueño(db.Model):
    __tablename__ = 'dueño'
    correo_dueño = db.Column(db.String(80), primary_key = True)
    username = db.Column(db.String(80),nullable = True)
    password = db.Column(db.String(80),nullable =True)
    contacto =  db.Column(mysql.BIGINT,nullable = True) 
    idioma = db.Column(db.String(20),nullable = True)


    viviendasU = db.relationship("Vivienda",back_populates="dueño")


class Solicitud(db.Model):
    __tablename__="solicitud"
    codigo_Solicitud =  db.Column(db.Integer, primary_key=True)
    estudiante_correo = db.Column(Integer, ForeignKey('estudiante.correo_estudiante'))
    codigo_vivienda = db.Column(Integer, ForeignKey('vivienda.codigo_Vivienda'))
    estado = db.Column(db.String(80),nullable = True)
    fecha_entrada = db.Column(db.String(80),nullable = True)
    fecha_salida = db.Column(db.String(80),nullable = True)
    forma_pago = db.Column(db.String(80),nullable = True)


    estudiante = relationship("Estudiante", backref=backref("vivienda_assoc"))
    vivienda = relationship("Vivienda", backref=backref("estudiante_assoc"))


class Sitios_Interes(db.Model):
    __tablename__="sitios_interes"
    codigo_Interes = db.Column(db.Integer, primary_key=True)
    latitud_Interes = db.Column(db.String(80),nullable =True)
    longitud_Interes = db.Column(db.String(80),nullable =True)
    nombre_Interes = db.Column(db.String(80),nullable = True)
    descripcion_Interes = db.Column(db.String(120),nullable=True) 


    eventos = db.relationship("Evento",back_populates="sitio")


class Evento(db.Model):
    __tablename__="evento"
    codigo_evento = db.Column(db.Integer, primary_key=True)
    nombre_evento = db.Column(db.String(80),nullable =True)
    descripcion_evento = db.Column(db.String(80),nullable =True)
    fecha = db.Column(db.String(80),nullable =True)
    hora = db.Column(db.String(80),nullable =True)
    abierta_publico = db.Column(db.String(80),nullable =True)
    sitio_interes = db.Column(db.Integer,ForeignKey('sitios_interes.codigo_Interes'))
    correo_estudiante_dueño = db.Column(db.Integer,ForeignKey('estudiante.correo_estudiante'))
    

    estudiante_dueño = db.relationship("Estudiante",back_populates="evento")
    estudiantes = relationship("Estudiante",secondary=asistencia_evento)
    sitio = db.relationship("Sitios_Interes",back_populates="eventos")
    























#----- Todos los / -----

# Inicio del programa
@app.route("/",methods=['GET','POST'])
def inicio():
    estu = Estudiante.query.all()
    due = Dueño.query.all()

    for i in session:
        for k in due:
            if session[i] == k.correo_dueño:
                return render_template("base_dueño.html")   
        
    for i in session:
        for k in estu:
            if session[i] == k.correo_estudiante:
                return render_template("base_estudiante.html")             
        
    return render_template("base_sin_loguear.html")


#----- Mapa para los dueños -----
@app.route("/mapa",methods=['GET','POST'])
def mapa():
    if request.method == 'POST':
        #Guarda la vivienda en la bd
        y = request.form['latitud']
        x = request.form['longitud']
        print(y)
        print(x)

        c = Dueño.query.filter_by(correo_dueño = session["correo_dueño"]).first()
        new_vivienda = Vivienda(latitud = request.form['latitud'],longitud = request.form['longitud'],descripcion = request.form["descripcion"],reglas = request.form["reglas"],precio = request.form["precio"],tipo = request.form["tipo"],metodo_pago=request.form["metodo"],direccion_exacta = request.form["direccion_exacta"],dueño = c,estado = "t")
        db.session.add(new_vivienda)
        db.session.commit()
        flash("Tu vivienda se ha registrado exitosamente!.")
        return redirect("/")
        
    o = Vivienda.query.all()
    ubicaciones = []
    for i in o:
        if i.estado == "t":
            ubicaciones.append({"Latitud":i.latitud,"Longitud":i.longitud})


    return render_template("mapa_viviendas.html", ubi = ubicaciones)


#----- Mapa para el estudiante -----
@app.route("/mapaEstudiante",methods=['GET','POST'])
def mapaEstudiante():
    if request.method == 'POST':
        #Aca recibo el código de la vivienda
        codigo_vivienda = request.form['xd']

        #Agrego a la tabla Solicitud
        x = Solicitud.query.all()
        #Hago el código único para la solicitud
        codigo_SolicitudNew = None
        for u in x:
            codigo_SolicitudNew = u.codigo_Solicitud
        else:
            if codigo_SolicitudNew == None:
                codigo_SolicitudNew = 1

        #Guardo en la tabla solicitud
        i = Estudiante.query.filter_by(correo_estudiante = session["correo_estudiante"]).first()
        j = Vivienda.query.filter_by(codigo_Vivienda=codigo_vivienda).first()
        ij = Solicitud(estudiante = i,vivienda = j,estado ="Pendiente",codigo_Solicitud = codigo_SolicitudNew+1,fecha_entrada = request.form['fecha_entrada'],fecha_salida = request.form['fecha_salida'],forma_pago = request.form['forma_pago'])
        db.session.add(ij)
        db.session.commit()
        render_template("base.html")
        return '200'   

    #Envio las viviendas 
    g = Vivienda.query.all()
    ubicaciones = []
    for i in g:
        l = i.dueño.username
        k = i.dueño.correo_dueño
        if i.estado == "t":
            ubicaciones.append({"Num":i.codigo_Vivienda,"Latitud":i.latitud,"Longitud":i.longitud,"Dueño":l,"Correo_dueño":k,"Descripcion":i.descripcion,"Reglas":i.reglas,"Precio":i.precio,"Tipo":i.tipo,"Metodo":i.metodo_pago,"direccion_exacta":i.direccion_exacta})

    #Envio sitios de interes
    x = Sitios_Interes.query.all()
    sitios = []
    for i in x:
        sitios.append({"codigo":i.codigo_Interes,"latitud":i.latitud_Interes,"longitud":i.longitud_Interes,"descripcion":i.descripcion_Interes,"nombre_sitio":i.nombre_Interes}) 

    return render_template("mapa_estudiante.html",ubi = ubicaciones,sitios = sitios)


#----- Registro del estudiante: -----
@app.route("/registroEstudiante",methods=['GET','POST'])
def registro_estudiante():
    if request.method == 'POST':
        x = Estudiante.query.filter_by(correo_estudiante = request.form["correo"]).first()
        #Reviso si no esta en ninguna tabla ese correo
        y = Dueño.query.filter_by(correo_dueño = request.form["correo"]).first()
        if(x == None and y == None):
            hashed_pw=generate_password_hash(request.form["password"],method="sha256")
            new_estudiante = Estudiante(correo_estudiante = request.form["correo"],username = request.form["username"],password = hashed_pw,pais = request.form["pais"],genero = request.form["genero"],edad = request.form["edad"],idioma = request.form["idioma"],contacto=request.form["numero"])
            db.session.add(new_estudiante)
            db.session.commit()
            flash("Te has registrado exitosamente!.")
            return redirect("/login")
        else:
            if(x != None or y != None):
                flash("Ese correo ya existe, intenta con otro.")
                
        
    return render_template("registro_estudiante.html")


#----- Registro dueño ----- 
@app.route("/registroDueño",methods=['GET','POST'])
def registro_dueño():
    if request.method == 'POST':
        x = Dueño.query.filter_by(correo_dueño = request.form["correo"]).first()
        #Reviso si no esta en ninguna tabla ese correo
        y = Estudiante.query.filter_by(correo_estudiante = request.form["correo"]).first()
        if(x == None and y == None):
            hashed_pw=generate_password_hash(request.form["password"],method="sha256")
            new_dueño = Dueño(correo_dueño = request.form["correo"],username = request.form["username"],password = hashed_pw,contacto = request.form["contacto"],idioma = request.form["idioma"])
            db.session.add(new_dueño)
            db.session.commit()
            flash("Te has registrado exitosamente!.")
            return redirect("/login")
        else:
            if(x != None or y != None):
                flash("Ese correo ya existe, intenta con otro.")
    return render_template("registro_dueño.html")


#----- Registro de evento -----
@app.route("/eventos",methods=['GET','POST'])
def eventos():

    if request.method == 'POST':
        k = request.form['num']
        if k == "1":
            #Guarda en la tabla asistencia_evento
            s = Evento.query.filter_by(codigo_evento = request.form['id']).first()
            l = Estudiante.query.filter_by(correo_estudiante = session["correo_estudiante"]).first()
            s.estudiantes.append(l)
            db.session.add(s)
            db.session.commit()
        else:
            #Guardo en la tabla evento
            c = Estudiante.query.filter_by(correo_estudiante = session["correo_estudiante"]).first()
            o = Sitios_Interes.query.filter_by(codigo_Interes = request.form['xd']).first()
            new_evento = Evento(nombre_evento = request.form['nombre_evento'],descripcion_evento = request.form['descripcion_evento'],fecha = request.form['dia_evento'],hora = request.form['hora_evento'],abierta_publico = request.form['abierto'],estudiante_dueño = c,sitio = o)
            db.session.add(new_evento)
            db.session.commit()
            flash("El evento ha sido creado exitosamente!.")
        
        return redirect("/")

    x = Sitios_Interes.query.all()
    sitios = []
    for i in x:
        sitios.append({"codigo":i.codigo_Interes,"latitud":i.latitud_Interes,"longitud":i.longitud_Interes,"descripcion":i.descripcion_Interes,"nombre_sitio":i.nombre_Interes})

    y = Evento.query.all()
    eventos = []
    for i in y:
        eventos.append({"codigo_evento":i.codigo_evento,"nombre_evento":i.nombre_evento ,"descripcion_evento":i.descripcion_evento,"fecha":i.fecha,"hora":i.hora,"abierta_publico":i.abierta_publico,"estudiante_dueño":i.estudiante_dueño.username,"codigo_sitio_interes":i.sitio.codigo_Interes})

    return render_template("mapa_eventos.html",sitios = sitios,eventos = eventos)


#----- Login -----
@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == "POST":
        estudiante = Estudiante.query.filter_by(correo_estudiante=request.form["correo"]).first()
        dueño = Dueño.query.filter_by(correo_dueño = request.form["correo"]).first()
        #Login para estudiante
        if estudiante and check_password_hash(estudiante.password, request.form["password"]):

            session["correo_estudiante"] = estudiante.correo_estudiante
            session.pop("correo_dueño",None)
            return redirect("/")
        else:
            #Login para dueño
            if dueño and check_password_hash(dueño.password,request.form["password"]):

                session["correo_dueño"] = dueño.correo_dueño
                session.pop("correo_estudiante",None)
                return redirect("/")

    return render_template("login.html")


#----- Ver el perfil del estudiante -----
@app.route("/perfilEstudiante",methods=['GET','POST'])
def perfilEstudiante():
    x = Estudiante.query.filter_by(correo_estudiante=session["correo_estudiante"]).first()
   
    return render_template("perfil_estudiante.html",h = x)


#----- Ver el perfil del dueño -----
@app.route("/perfilDueño",methods=['GET','POST'])
def perfilDueño():
    if request.method == "POST":
        #Eliminar vivienda
        u = request.form['codigo']
        print(u)
        y = Solicitud.query.filter_by(codigo_vivienda = u).all()
        for i in y:
            db.session.delete(i)
            db.session.commit()

        x = Vivienda.query.filter_by(codigo_Vivienda = u).first()
        x.estado = "f"
        db.session.commit()



    h = Dueño.query.filter_by(correo_dueño = session["correo_dueño"]).first()
    u = Vivienda.query.join(historial).join(Estudiante).filter((historial.c.correo_estudiante == Estudiante.correo_estudiante) 
                                            & (historial.c.vivienda_id == Vivienda.codigo_Vivienda)).all()


    return render_template("perfil_dueno.html",h = h,u = u)


#----- Notificaciones dueño -----
@app.route("/notificacionesDueño",methods=['GET','POST'])
def notificacionesDueño():

    if request.method == 'POST':
        jn = request.form['id']
        r = request.form['num']
        if r == "1":
            z = Solicitud.query.filter_by(codigo_Solicitud = jn).first()
            #Cambio el estado de la solicitud
            z.estado = "Aceptado"
            db.session.commit()
            print(z.estudiante.correo_estudiante)
            print(z.vivienda.codigo_Vivienda)
            #Agrega a la tabla historial
            s = Vivienda.query.filter_by(codigo_Vivienda = z.vivienda.codigo_Vivienda).first()
            c = Estudiante.query.filter_by(correo_estudiante = z.estudiante.correo_estudiante).first()
            c.viviendas.append(s)
            db.session.add(c)
            db.session.commit()

        if r == "0":
            z = Solicitud.query.filter_by(codigo_Solicitud = jn).first()
            #Cambio el estado de la solicitud
            print(z)
            z.estado = "Rechazado"
            db.session.commit() 

        return '200'

    #----- Envio las solicitudes -----

    x = Solicitud.query.all()
    solicitudes = []
    for i in x:
        solicitudes.append({"Estudiante":i.estudiante,"Vivienda":i.vivienda,"estado":i.estado,"codigo_Solicitud":i.codigo_Solicitud,"fecha_entrada":i.fecha_entrada,"fecha_salida":i.fecha_salida})
        

    return render_template("notificaciones_dueños.html",solicitudes = solicitudes,dueño_actual = session["correo_dueño"])


#----- Notificaciones estudiante -----
@app.route("/notificacionesEstudiante",methods=['GET','POST'])
def notificacionesEstudiante():

    #----- Envio las solicitudes -----
    x = Solicitud.query.all()
    solicitudes = []
    
    for i in x:
        solicitudes.append({"Estudiante":i.estudiante,"Vivienda":i.vivienda,"estado":i.estado,"codigo_Solicitud":i.codigo_Solicitud})

    return render_template("notificaciones_estudiante.html",solicitudes = solicitudes, estudiante_actual = session["correo_estudiante"])


#----- Notificaciones estudiante -----
@app.route("/mapaSitiosInteres",methods=['GET','POST'])
def mapaSitiosInteres():
    if request.method == 'POST':
        #Guarda el sitio de interes en la bd
        y = request.form['latitud']
        p = request.form['longitud']
        print(y)
        print(p)
        new_sitio = Sitios_Interes(latitud_Interes = y,longitud_Interes=p,nombre_Interes=request.form['nombre_sitio'],descripcion_Interes=request.form['descripcion_sitio'])
        db.session.add(new_sitio)
        db.session.commit()
        flash("El sitio de interes se ha registrado exitosamente!.")
        return redirect("/")

    x = Sitios_Interes.query.all()
    sitios = []

    for i in x:
        sitios.append({"codigo":i.codigo_Interes,"latitud":i.latitud_Interes,"longitud":i.longitud_Interes,"descripcion":i.descripcion_Interes,"nombre_sitio":i.nombre_Interes})

    return render_template("mapa_sitios_interes.html",sitios = sitios)


#----- Cerrar sesion -----
@app.route("/logout",methods=['GET','POST'])
def logout():
    if request.method == 'POST':
        session.pop("correo_estudiante",None)
        session.pop("correo_dueño",None)

    return redirect("/")

















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
        i.estado = "Aceptado"
        db.session.commit()
        print(i.estado)
        print(i.vivienda.dueño)
        print(i.vivienda.reglas)

    return "REVISA LA CONSOLA"


@app.route("/probarNose1",methods=['GET','POST'])
def probarNose1():
    #x = Estudiante.query.filter_by(correo_estudiante = "xahepjulian45@gmail.com").first()
    x =Vivienda.query.filter_by(codigo_Vivienda = 1).first()

    print(x.dueño)

    return "Consolo"


@app.route("/probarNose2",methods=['GET','POST'])
def probarNose2():
    if request.method == 'POST':
        x = request.form['id']
        k = request.form['num']
        print("Este nnúmero me llega de envenos"+ k)
        print(x)

    return "Mira la consola"





























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


#----- Ir al mapa de sitios de interes ----
@app.route("/irMapaSitioInteres",methods=["GET","POST"])
def irMapaSitioInteres():
    if request.method == "POST":
        return redirect("/mapaSitiosInteres")


#----- Ir a mapa eventos ----
@app.route("/irMapaEventos",methods=["GET","POST"])
def irMapaEventos():
    if request.method == "POST":
        return redirect("/eventos")





















app.secret_key = "12345"

if __name__=="__main__":
    db.create_all()
    app.run(debug=True)
