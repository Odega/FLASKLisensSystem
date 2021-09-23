import flask
from flask import Flask, Blueprint, render_template, session, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_material import Material
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import itertools
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
# Fil med alt om MYSQL databasen
from lisensAPI.databaseFile import Database, addDatabase, getStudentCourses
from .models import Kommuner, Note, SchoolNote, Courses, User
from . import db

views = Blueprint('views', __name__)

# Hoveddashbord
@views.route("/")
@views.route("/dashboard")
@login_required
def dashboard():
    ### PROD ###
    query = "SELECT * from lisenser ORDER BY id desc;"
    validQuery = "SELECT kommune, skoleNavn, LMnavn, DATEDIFF(lastValid,CURDATE()), orgNr FROM (SELECT kommune, skoleNavn, LMnavn, validTo as lastValid, orgNr, MAX(createdDate) FROM lisenser WHERE signatur != 'DemoButikk' GROUP BY skoleNavn, LMnavn) as a WHERE DATEDIFF(lastValid,CURDATE()) < 30 AND DATEDIFF(lastValid,CURDATE()) > 0;"
    ############
    ### TEST ###
    #query = "SELECT * from lisenser_test ORDER BY id desc;" 
    #validQuery = "SELECT kommune, skoleNavn, LMnavn, DATEDIFF(lastValid,CURDATE()), orgNr FROM (SELECT kommune, skoleNavn, LMnavn, validTo as lastValid, orgNr, MAX(createdDate) FROM lisenser_test WHERE signatur != 'DemoButikk' GROUP BY skoleNavn, LMnavn) as a WHERE DATEDIFF(lastValid,CURDATE()) < 30 AND DATEDIFF(lastValid,CURDATE()) > 0;"
    ############

    allInfo = Database(query)
   
    validInfo = Database(validQuery)
    if validInfo is not ():
        validSorted = sortValidMe(json.loads(json.dumps(validInfo)))
    else:
        #print("Valid er TOM")
        validSorted = None

    courseList = getOurCourses()

    return render_template("dashboard.html", resultat=allInfo, validResultat=validSorted, user=current_user, courseList=courseList)

# Side for skoler


@views.route("/skole/<school>", methods=["GET", "POST"])
@login_required
def school_page(school):
    if request.method == 'POST':
        scl_nt = request.form.get('school_note')
        org_nr = request.form.get('school_org')
        if len(scl_nt) < 1:
            flash('Du må skrive noe...', category='error')
        else:
            new_school_note = SchoolNote(data=scl_nt, org_id=org_nr , username = current_user.username)
            db.session.add(new_school_note)
            db.session.commit()
            flash("Notat lagt til!", category='success')

    query = "SELECT * from lisenser WHERE skoleNavn = '{}';".format(school)

    res = Database(query)
    #print(request.args)
    orgNr = request.args['orgNr']
    kommune = request.args['kommune']
    #SQLALCHEMY
    #result = select(username, data, date, org_id).where(org_id == orgNr).fetchall() 
    result = SchoolNote.query.filter_by(org_id=orgNr).order_by(SchoolNote.date.desc()).all()

    courseList = getOurCourses()
    return render_template("school.html", resultat=res, schoolName=school, orgNr=orgNr, kommune=kommune, skole_notater = result, courseList = courseList, user=current_user)

# Side for kommune


@views.route("/kommune/<kommune>", methods=["GET", "POST"])
@login_required
def kommune_page(kommune):
    #print("KOMMUNE PAGE")
    query = "SELECT * from lisenser WHERE kommune = '{}';".format(kommune)
    #print("QUERY: {}".format(query))
    res = Database(query)
    courseList = getOurCourses()
    return render_template("kommune.html", resultat=res, kommuneNavn=kommune, courseList = courseList, user=current_user)

# Side for læremidler


@views.route("/coursemanager", methods=['GET', 'POST'])
@login_required
def course_manager():
    courseList = getOurCourses()

    if request.method == 'POST':
        if request.form.get('_METHOD') == 'POST':
            print("POST TIME")
            scourseId = request.form.get('courseId')
            scourse = request.form.get('course')
            ssection = request.form.get('section')
            lisence = Courses(courseId=scourseId, course=scourse, section=ssection)
            db.session.add(lisence)
            db.session.commit()
            return redirect(url_for('views.course_manager'))

        elif request.form.get('_METHOD') == 'DELETE':
            print("DELETION TIME!")
            scourseId2 = request.form.get('courseId2')
            scourse = request.form.get('course2')
            ssection = request.form.get('section2')
            lisence = Courses.query.filter_by(courseId=scourseId2).first()
            db.session.delete(lisence)
            db.session.commit()
            return redirect(url_for('views.course_manager'))

        elif request.form.get('_METHOD') == 'EDIT':
            print("EDIT TIME!")
            prevId = request.form.get('prevId')
            scourseId2 = request.form.get('courseId')
            scourse = request.form.get('course')
            ssection = request.form.get('section')
            print(prevId)
            print(scourseId2)
            print(scourse)
            print(ssection)
            lisence = Courses.query.filter_by(courseId=prevId).first()
            lisence.courseId = scourseId2
            lisence.course = scourse
            lisence.section = ssection
            db.session.commit()
            return redirect(url_for('views.course_manager'))

    return render_template("course_manager.html", courseList=courseList, user=current_user)

# Side for skoler

@views.route("/schoolmanager", methods=['GET', 'POST'])
@login_required
def school_manager():
    schoolList = getOurSchools()

    if request.method == 'POST':
        if request.form.get('_METHOD') == 'POST':
            print("POST TIME")
            org = request.form.get('addOrgNr')
            skl = request.form.get('addSkole')
            kom = request.form.get('addKommune')

            skoleOrg = Kommuner.query.filter_by(orgNr=org).first()
            if(skoleOrg is not None):
                flash("Skole med dette orgnummeret eksisterer allerede!", category='error')
                return redirect(url_for('views.school_manager'))
            skole = Kommuner(orgNr = org, skoleNavn = skl, kommuneNavn=kom)
            
            db.session.add(skole)
            db.session.commit()
            return redirect(url_for('views.school_manager'))

        elif request.form.get('_METHOD') == 'DELETE':
            print("DELETION TIME!")
            org = request.form.get('delOrg')
            skl = request.form.get('delSkole')
            kom = request.form.get('delKom')
            skole = Kommuner.query.filter_by(orgNr=org).first()
            db.session.delete(skole)
            db.session.commit()
            return redirect(url_for('views.school_manager'))

    return render_template("school_manager.html", schoolList=schoolList, user=current_user)

# Side for brukerhåndtering

@views.route("/usermanager", methods=['GET', 'POST'])
@login_required
def user_manager():
    userList = getOurUsers()

    if request.method == 'POST':
        if request.form.get('_METHOD') == 'POST':
            print("POST TIME")
            susername = request.form.get('username')
            semail = request.form.get('email')
            ssign = request.form.get('signatur')
            spassword = request.form.get('password')
            pWord = generate_password_hash(spassword, method='sha256')
            user = User(username=susername, email=semail, sign=ssign, password=pWord)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('views.user_manager'))

        elif request.form.get('_METHOD') == 'DELETE':
            print("DELETION TIME!")
            susername = request.form.get('username')
            user = User.query.filter_by(username=susername).first()
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('views.user_manager'))

        elif request.form.get('_METHOD') == 'EDITPW':
            print("EDITTIME!")
            susername = request.form.get('username2')
            user1 = User.query.filter_by(username=susername).first()
            pw1 = request.form.get('password')
            pw2 = request.form.get('password2')
            if pw1 != pw2:
                print("NOT SAME PW")
            else:
                pWord = generate_password_hash(pw1, method='sha256')
                user1.password = pWord
                db.session.commit()
            return redirect(url_for('views.user_manager'))

    return render_template("user_manager.html", userList=userList, user=current_user)

# Side for utågtte lisenser

@views.route("/expired", methods=["GET"])
@login_required
def expired():
    
    query = "SELECT kommune, skoleNavn, LMnavn, DATEDIFF(lastValid,CURDATE()), orgNr, lastValid FROM (SELECT id, kommune, skoleNavn, LMnavn, validTo as lastValid, orgNr, MAX(createdDate) FROM lisenser GROUP BY skoleNavn, LMnavn) as a WHERE DATEDIFF(lastValid,CURDATE()) < 0;"

    validInfo = Database(query)

    if validInfo is not ():
        #print("SORTERER...")
        validSorted = sortValidMe(json.loads(
            json.dumps(validInfo, default=str)))
        #print("SORTERT")
    else:
        #print("Valid er TOM")
        validSorted = None
    courseList = getOurCourses()
    return render_template("expired.html",  validResultat=validSorted, courseList=courseList, user=current_user)

#Side for notater


@views.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Du må skrive noe...', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash("Notat lagt til!", category='success')

    return render_template("notes.html", user=current_user)
#Slett note
@views.route("/delete-note", methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

#Slett skolenote
@views.route("/delete-school-note", methods=['POST'])
def delete_school_note():
    note = json.loads(request.data)
    schoolNoteId = note['noteId']
    note = SchoolNote.query.get(schoolNoteId)
    if note:
        db.session.delete(note)
        db.session.commit()

    return jsonify({})


# Legg til Lisens i Database (Skole enkel)


@views.route("/addToDB", methods=["GET", "POST"])
def addToDB():
    #print("-----------addToDB------------")
    jsonData = request.get_json()

    # Antall rader
    rader = len(jsonData["lMiddelVal"])

    insertArray = []
    # Insert query
    orgNr = jsonData["orgNr"]
    kommune = jsonData["kommune"]
    skoleNavn = jsonData["skoleNavn"]
    genDate = jsonData["genDate"]
    valDate = jsonData["valDate"]
    sign = jsonData["sign"]
    now = datetime.datetime.now()
    feil = lisensFeil(orgNr, kommune, skoleNavn)
    if feil:
        flash('Du må fylle ut alle feltene!', category='error')
        return json.dumps({'success':False}), 500, {'ContentType':'application/json'} 

    for x in range(rader):
        insertArray.append(
            (
                orgNr,
                kommune,
                skoleNavn,
                jsonData["lMiddelText"][x],
                jsonData["lMiddelVal"][x],
                genDate,
                valDate,
                sign,
                now.strftime('%Y-%m-%d'),
            )
        )
    logging.debug('-----------------------insertArray---------------------')
    print(insertArray)
    addDatabase(insertArray)
    flash('Skolelisenser lagt til.', category='success')
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

# Legg til Lisens i Database (Skole multi)


@views.route("/addToDBMulti", methods=["GET", "POST"])
def addToDBMulti():
    #print("-----------addToDB------------")
    jsonData = request.get_json()

    # Antall rader LM
    raderLM = len(jsonData["lMiddelVal"])

    # Antall rader Skole
    raderSkole = len(jsonData["skoleNavn"])

    insertArray = []
    # Insert query
    orgNr = jsonData["orgNr"] #array
    kommune = jsonData["kommune"]
    skoleNavn = jsonData["skoleNavn"] #array
    genDate = jsonData["genDate"]
    valDate = jsonData["valDate"]
    sign = jsonData["sign"]
    now = datetime.datetime.now()
    #feil = lisensFeil(orgNr, kommune, skoleNavn)
    #if feil:
    #    flash('Du må fylle ut alle feltene!', category='error')
    #    return json.dumps({'success':False}), 500, {'ContentType':'application/json'} 

    for y in range(raderSkole):
        for x in range(raderLM):
            insertArray.append(
                (
                    jsonData["orgNr"][y], #orgNr[y],
                    kommune,
                    jsonData["skoleNavn"][y], #skoleNavn[y],
                    jsonData["lMiddelText"][x],
                    jsonData["lMiddelVal"][x],
                    genDate,
                    valDate,
                    sign,
                    now.strftime('%Y-%m-%d'),
                )
            )
    logging.debug('-----------------------insertArray---------------------')
    print(insertArray)
    addDatabase(insertArray)
    flash('Skolelisenser lagt til.', category='success')
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 


# Legg til Lisens i Database (Kommune)


@views.route("/addToDBKom", methods=["GET", "POST"])
def addToDBKom():
    #print("-----------addToDB KOMMUNE------------")
    jsonData = request.get_json()

    # Antall rader PR SKOLE
    LMRader = len(jsonData["lMiddelVal"])

    skoleList = getSchools(jsonData["kommune"])

    insertArray = []

    kommune = jsonData["kommune"]
    genDate = jsonData["genDate"]
    valDate = jsonData["valDate"]
    sign = jsonData["sign"]
    now = datetime.datetime.now()
    
    # FOR HVER SKOLE I KOMMUNEN
    for i in skoleList:
        # FOR HVERT LM TIL SKOLEN
        for x in range(LMRader):
            insertArray.append(
                (
                    i[0],
                    kommune,
                    i[1],
                    jsonData["lMiddelText"][x],
                    jsonData["lMiddelVal"][x],
                    genDate,
                    valDate,
                    sign,
                    now.strftime('%Y-%m-%d'),
                )
            )
    #print("Adding to DB")
    addDatabase(insertArray)
    #print("Packed and sendt to add")
    flash('Kommunelisenser lagt til.', category='success')
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 


# Legg til Lisens i Database (Tilpasset)


@views.route("/addToDBCustom", methods=["GET", "POST"])
def addToDBCustom():
    #print("-----------addToDB------------")
    jsonData = request.get_json()

    insertArray = []
    # Insert query
    orgNr = jsonData["orgNr"]
    kommune = jsonData["kommune"]
    skoleNavn = jsonData["skoleNavn"]
    lMiddelId = jsonData["lMiddelVal"]
    lMiddel = jsonData["lMiddelText"]
    genDate = jsonData["genDate"]
    valDate = jsonData["valDate"]
    sign = jsonData["sign"]
    now = datetime.datetime.now()
    feil = lisensFeil(orgNr, kommune, skoleNavn)

    LMRader = len(jsonData["lMiddelVal"])

    if feil:
        flash('Du må fylle ut alle feltene!', category='error')
        return json.dumps({'success':False}), 500, {'ContentType':'application/json'} 
    print(orgNr,
            kommune,
            skoleNavn,
            lMiddel,
            lMiddelId,
            genDate,
            valDate,
            sign,
            now.strftime('%Y-%m-%d'))
    #print("IKKE FEIL.")
    for x in range(LMRader):
        #print("LMRADER FOR LOOP")
        insertArray.append(
            (
                orgNr,
                kommune,
                skoleNavn,
                jsonData["lMiddelText"][x],
                jsonData["lMiddelVal"][x],
                genDate,
                valDate,
                sign,
                now.strftime('%Y-%m-%d'),
            )
        )
    #print('-----------------------insertArray---------------------')
    #print(insertArray)
    addDatabase(insertArray)
    flash('Lisenser lagt til.', category='success')
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

# Ser etter feil i lisensopprettelse

def lisensFeil(org, kommune, skole):
    if(org is None or org is ''): return True
    if(kommune is None or kommune is ''): return True
    if(skole is None or skole is ''): return True
    return False

# Henter våre læremidler

def getOurCourses():
    metadata = db.MetaData()
    coursess = db.Table('courses', metadata)
    # Henter læremidler fra databasen
    
    res = db.session.query(Courses.metadata.tables['courses']).order_by(Courses.section, Courses.course.desc()).all()
    return res

# Henter våre brukere

def getOurUsers():
    metadata = db.MetaData()
    userss = db.Table('user', metadata)

    # Henter brukere fra databasen
    res = db.session.query(User.metadata.tables['user']).all()
    return res

# Henter våre skoler

def getOurSchools():
    metadata = db.MetaData()
    kommunerr = db.Table('kommuner', metadata)

    # Henter skoler fra databasen
    res = db.session.query(Kommuner.metadata.tables['kommuner']).order_by(Kommuner.kommuneNavn.asc()).all()
    return res

# Henter skoler ut i fra kommunenavn


def getSchools(kommune):
    metadata = db.MetaData()
    kommunerr = db.Table('kommuner', metadata)

    # Henter skoler fra databasen
    res = db.session.query(Kommuner.metadata.tables['kommuner']).filter_by(
        kommuneNavn=kommune).all()

    return res  # resultat


def sortValidMe(res):
    #print("RES: {}".format(res))
    firstElem = {}
    returnDict = []
    tmpList = []
    added = False
    if len(res[0]) == 5:
        firstElem = {
            'skole': res[0][1],
            'kommune': res[0][0],
            'gDager': res[0][3],
            'lm': [
                res[0][2]
            ],
            'orgNr': res[0][4]
        }
        #rint("FIRSTELEM LENGTH 5")
    elif len(res[0]) == 6:
        firstElem = {
            'skole': res[0][1],
            'kommune': res[0][0],
            'gDager': res[0][3],
            'lm': [
                res[0][2]
            ],
            'orgNr': res[0][4],
            'valDato': res[0][5]
        }
        #print("FIRSTELEM LENGTH 6")
    else:
        print("NOE FEIL!!! FIRSTELEM")
    returnDict.append(firstElem)

    # X er lise i RES
    for x in res[1:]:
        # y er skolenavn i x
        for dic in returnDict:
            for key, value in dic.items():
                # Skole finnes
                if key == 'skole' and value == x[1]:
                    added = True
                    # Dager er det samme
                    if dic['gDager'] == x[3]:
                        dic['lm'].append(x[2])
                    # Dager er ulike
                    else:
                        newElem = createElem(x)
                        tmpList.append(newElem)
        if added == False:
            newElem = createElem(x)
            tmpList.append(newElem)
        added = False

        if len(tmpList) > 0:
            returnDict.append(tmpList[0])
            tmpList = []
    returnedDict = sorted(returnDict, key=lambda i: i['gDager'])
    return returnedDict


def createElem(x):
    elem = {}
    if len(x) == 5:
        elem = {
            'skole': x[1],
            'kommune': x[0],
            'gDager': x[3],
            'lm': [
                x[2]
            ],
            'orgNr': x[4]
        }
    elif len(x) == 6:
        elem = {
            'skole': x[1],
            'kommune': x[0],
            'gDager': x[3],
            'lm': [
                x[2]
            ],
            'orgNr': x[4],
            'valDato': x[5]
        }
    else:
        print("NOE FEIL!!! CREATEELEM")
    return elem

# background process happening without any refreshing


@views.route("/background_process", methods=['GET', 'POST'])
def background_process():
    retDict = {}
    data = request.get_json()
    kom = data['kommune']

    metadata = db.MetaData()
    kommunerr = db.Table('kommuner', metadata)

    # Henter skoler fra databasen
    res = db.session.query(Kommuner.metadata.tables['kommuner']).filter_by(
        kommuneNavn=kom).all()

    for x in res:
        retDict[x[1]] = ""

    return retDict


@views.route("/background_process2", methods=['GET', 'POST'])
def background_process2():
    retOrg = ""
    data = request.get_json()
    skole = data['skoleNavn']
    kom = data['komNavn']

    metadata = db.MetaData()
    kommunerr = db.Table('kommuner', metadata)

    # Henter skoler fra databasen
    res = db.session.query(Kommuner.metadata.tables['kommuner']).filter_by(
        skoleNavn=skole, kommuneNavn=kom).first()
    try:
        retOrg = res[0]
    except:
        print("fant ikke..")
    print("retOrg = {}".format(retOrg))

    return retOrg

@views.route("/background_process3", methods=['GET', 'POST'])
def background_process3():
    
    dataTot = request.get_json()
    data = dataTot['skoleArr']
    d = jsonify(data)
    #print("----")
    #print(data)
    kom = dataTot['kommuneNavn']
    
    metadata = db.MetaData()
    kommunerr = db.Table('kommuner', metadata)

    retArr = []
    for f in data:

        res = db.session.query(Kommuner.metadata.tables['kommuner']).filter_by(
            skoleNavn=f, kommuneNavn=kom).first()
        try:
            retArr.append(res[0])

        except:
            print("fant ikke..")
            retArr.append("000")
            flash('Ett eller flere skolenavn finnes ikke i katalogen.', category='error')

    #print("returnerer retArr");
    #print(retArr)
    return jsonify(retArr)
