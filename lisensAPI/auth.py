from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random, string
from flask_mail import Mail, Message
from .models import User
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Suksess! Logget inn i systemet :)', category='success')
                return redirect(url_for('views.dashboard'))
            else:
                flash('Feil passord...', category='error')
        else:
            flash('Feil brukernavn. Brukeren eksisterer ikke i databasen..', category='error')

    return render_template('login.html', user=current_user)

# Logg ut

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Du er nå logget ut av systemet. Ha en fin dag :)', category='success')
    return redirect(url_for('auth.login'))

# Endre passord

@auth.route('/changepw', methods=['GET', 'POST'])
@login_required
def changepw():
    if request.method == 'POST':
        oldpw = request.form.get('oldpw')
        password1 = request.form.get('newpassword1')
        password2 = request.form.get('newpassword2')
        if(password1 == password2):
            user = User.query.filter_by(username=current_user.username).first()
            if check_password_hash(user.password, oldpw):
                print("Passord {}".format(password1))
                pw = generate_password_hash(password1, method='sha256')
                user.password = pw
                db.session.add(user)
                db.session.flush()
                db.session.commit()
                flash('Passordet er endret!', category='success')
                return redirect(url_for('views.dashboard'))
            else:
                flash('Gammelt passord stemmer ikke.', category='error')
        else:
            flash('Du har ikke skrevet samme passord to ganger.', category='error')


    return render_template('changepw.html', user=current_user)

# Glemt passord

@auth.route('/forgotpass', methods=['GET', 'POST'])
def forgotpass():
    if request.method == 'GET':
        #return '<form action="/forgotpass" method="POST"><input name="email"><input type="submit"></form>'
        return render_template('forgotpassword.html')
    
    # Finner bruker
    user = User.query.filter_by(email=request.form['email']).first()
    if user is None:
        print("user=none")
        flash("Fant ingen epost lik {} i databasen".format(request.form['email']), category='error')
        return redirect(request.url)

    # Random passord
    pw = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))

    # Oppdaterer i database
    nyttPw = generate_password_hash(pw, method='sha256')
    user.password = nyttPw
    db.session.add(user)
    db.session.flush()
    db.session.commit()

    # Sender epost
    msg = Message("Tilbakestill passord",
                  sender=("Lisensportal","kunnskap@kunnskap.no"),
                  recipients=[request.form['email']])
    msg.body ="Nytt passord er {}".format(pw)
    with current_app.app_context():
        mail = Mail(current_app)
        mail.send(msg)

    #return 'Eposten er sendt til: {}'.format(request.form['email'])
    flash("E-post sendt med nytt passord til {}".format(request.form['email']), category='success')
    return redirect(url_for('views.dashboard'))


# Legge til brukere i databasen

#@auth.route('/addUser/<username>/<password>/<sign>')
#def password(username, password, sign):
#    uName = username
#    pWord = generate_password_hash(password, method='sha256')
#    sN = sign
#    new_user = User(username=uName, password=pWord, sign=sN)
#    print("Legger til ny bruker")
#    db.session.add(new_user)
#    db.session.commit()
#    return 'user created...'
