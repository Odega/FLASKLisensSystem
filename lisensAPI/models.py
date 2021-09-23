from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    sign = db.Column(db.String(10))
    email = db.Column(db.String(30))
    notes = db.relationship('Note')

class Kommuner(db.Model):
    orgNr = db.Column(db.String(150), primary_key=True)
    skoleNavn = db.Column(db.String(150))
    kommuneNavn = db.Column(db.String(150))
    school_note = db.relationship('SchoolNote')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id= db.Column(db.Integer, db.ForeignKey('user.id'))

class SchoolNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    org_id= db.Column(db.Integer, db.ForeignKey('kommuner.orgNr'))

class Courses(db.Model):
    courseId = db.Column(db.Integer, primary_key=True)
    course = db.Column(db.String(50))
    section = db.Column(db.String(20))