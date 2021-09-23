from flask import Flask, Blueprint, render_template, session, request, jsonify, redirect, url_for, flash, current_app, abort
from flask_material import Material
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import random, string
from flask_mail import Mail, Message
# Fil med alt om MYSQL databasen
from .databaseFile import Database, addDatabase, getStudentCourses
from .models import Kommuner
from . import db

api = Blueprint('api', __name__)

######### API #################

#Learnetic API endpoint

@api.route("/api/v1/user-acess/acess-list/<secretKey>/<userId>", methods=["POST"])
def fin(secretKey, userId):
    jsonData = request.get_json()
    skoleId = jsonData["schoolId"]
    secret = secretKey
    user = userId
    json_output = json.dumps(jsonData)

    if secret == current_app.config['L_SECRET']:
        courses = getStudentCourses(skoleId)
        return {"courses": courses}
    else:
        return """ WRONG SECRET """
        #return Response("{'Secret':'Wrong'}", status=404, mimetype='application/json'


#Kunnskap Butikk - Gratis utprøving
# EKS
# URL: https://api.kunnskap.no/api/v1/butikk/utproving/BrettMatte
#{
#    "SECRET_KEY": "...all(i)",
#    "kommune": "Tromsø",
#    "schoolName": "Kvaløysletta skole"
#    "email" : "test@kunnskap.no"
#}

@api.route("/api/v1/butikk/utproving/<laeremiddel>", methods=["POST"])
def provut(laeremiddel):
    jsonData = request.get_json()
    secret = jsonData["SECRET_KEY"]
    kommune = jsonData["kommune"]
    skoleNavnVal = jsonData["schoolName"]
    epost = jsonData["email"]
    json_output = json.dumps(jsonData) 
    orgNrVal = ""
    now = datetime.datetime.now()

    ## Noen sjekker for å se at kom og skole eksisterer i db
    org = Kommuner.query.filter_by(skoleNavn=skoleNavnVal).first_or_404(description='Ingen skole med navnet {}'.format(skoleNavnVal))
    kom = Kommuner.query.filter_by(kommuneNavn=kommune).first_or_404(description='Ingen kommune med navnet {}'.format(kommune))
    if(org.kommuneNavn == kommune):
        orgNrVal = org.orgNr
    else:
        return {
            abort(404, 'Kommune og skole samsvarer ikke.')
        }
    
    dagensDato = now.strftime('%Y-%m-%d')
    datoPluss = datetime.datetime.strptime(dagensDato, '%Y-%m-%d')
    datoPlussUke = datoPluss + datetime.timedelta(days=7)
    lmId = "6095474545131520"
    query = [(orgNrVal, kommune, skoleNavnVal, laeremiddel, lmId, dagensDato, datoPlussUke, "DemoButikk", dagensDato)]
    #return {
    #    "query": query
    #}
    if secret == current_app.config['KBP_SECRET']:
        addDatabase(query)
        sendDemoEmail(laeremiddel, epost)
        return {"message": "Added {} to database".format(query)}
    else:
        return """ WRONG SECRET """

# Non encryption test


@api.route("/api/v1/user-acess/acess-list/<userId>", methods=["GET", "POST"])
def apiGetCourses(userId):

    return jsonify({"msge": userId})
##############################
# Sender til epostDEMOBRUKER 
def sendDemoEmail(lm,em):

    msg = Message("{} er nå lagt til i dine læremidler".format(lm),
                  sender=("Min Kunnskap - Demo","kunnskap@kunnskap.no"),
                  recipients=[em])
    msg.body ="Logg inn på min.kunnskap.no for å bruke {} gratis i én uke!".format(lm)
    with current_app.app_context():
        mail = Mail(current_app)
        mail.send(msg)
    
    return """ok"""