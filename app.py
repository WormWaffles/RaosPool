from flask import Flask, render_template, request, redirect, url_for, flash, session, g, abort
import requests
import os
from src.models import db, Member, Emp, Code, Membership
from src.members import members
from src.emps import emps
from src.codes import codes
from src.memberships import memberships
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import uuid
import re



app = Flask(__name__)

# database connection
load_dotenv()

db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] \
    = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True # set to True to see SQL queries
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max upload size

db.init_app(app)


# variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Use an app-specific password if necessary
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('DEFAULT_SENDER')
mail = Mail(app)

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


# AWS S3 connection (for member photos)

# check if the user is logged in
@app.before_request
def before_request():
    g.user = None
    if 'email' in session:
        g.user = session['email']

def send_email(email, subject, body):
    # code = codes.create_code(email=email)
    # token = Code.get_email_token(code)
    msg = Message(subject, sender='colin8297@gmail.com', recipients=[email])
    msg.body = f'{body}'
    mail.send(msg)


@app.route('/')
def index():
    return render_template('/index.html', g=g, home=True)

@app.route('/events')
def events():
    # get all files from static/images/events
    files = os.listdir('static/images/events')
    # get the file names
    images = [f for f in files if os.path.isfile(os.path.join('static/images/events', f))]
    return render_template('events.html', events=True, images=images)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html', pricing=True)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        email = request.form.get('email')
        message = request.form.get('message')

        if first_name == '' or last_name == '' or email == '' or message == '':
            flash('Please fill out all fields', 'error')
            return render_template('contact.html', contact=True)
        
        message = f'Name: {first_name} {last_name}\nEmail: {email}\n\nInquiry: {message}'

        send_email(os.getenv('CONTACT_RECEIVER'), f'Inquiry from {first_name} {last_name}', message)
        return render_template('confirmation.html', message='Thanks for your feedback, your message has been sent', sub_message='We will get back to you as soon as possible')

    return render_template('contact.html', contact=True)

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        # get email from user
        email = request.form['email']
        if not email:
            flash('Email is required', 'error')
            return render_template('join.html')
        if not re.fullmatch(regex, email):
            flash('Invalid email', 'error')
            return render_template('join.html')
        # check if email is already in use
        if members.get_membership_by_email(email):
            flash('Email is already in use', 'error')
            return render_template('join.html')
        # add email to codes table
        if codes.get_code_by_email(email):
            codes.delete_code(email)
        # send email to user
        code = codes.create_code(email=email)
        token = Code.get_email_token(code)
        message = f'''
Click the link to create your membership: 
{url_for("create", token=token, _external=True)}

If you did not make this request, ignore this email.
        '''

        send_email(email, "Rao's: finish application", message)
        return render_template('confirmation.html', message = f'Thanks! We sent an email to {email}', sub_message='Please check your email to complete your membership')
    return render_template('join.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # get form info
        inputs = {}
        try:
            inputs['fname'] = request.form['fname']
            inputs['lname'] = request.form['lname']
            email = request.form['email']
            inputs['phone'] = request.form['phone']
            inputs['dob'] = request.form['dob']
            inputs['size_of_family'] = request.form['size_of_family']
            inputs['password'] = request.form['password']
            inputs['street'] = request.form['street']
            inputs['city'] = request.form['city']
            inputs['state'] = request.form['state']
            inputs['zip_code'] = request.form['zip']
            inputs['membership_type'] = int(request.form['option'])
            inputs['referred_by'] = request.form['referred_by']
            inputs['emergency_contact_name'] = request.form['emergency_contact_name']
            inputs['emergency_contact_phone'] = request.form['emergency_contact_phone']
            if request.form['agree'] != 'on':
                flash('Please agree to the terms and conditions', 'error')
                return render_template('create.html', email=email, inputs=inputs)
        except:
            flash('Please fill out all fields', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        for key, value in inputs.items():
            if value == '':
                flash('Please fill out all fields', 'error')
                return render_template('create.html', email=email, inputs=inputs)
        if inputs['zip_code'].isdigit() == False:
            flash('Invalid zip code', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        if len(inputs['zip_code']) != 5:
            flash('Invalid zip code', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        if inputs['membership_type'] not in [1, 2, 3]:
            flash('Invalid membership type, please select a box.', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        if not re.fullmatch(regex, email):
            flash('Invalid email', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        if len(inputs['password']) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        inputs['phone'] = re.sub(r'\D', '', inputs['phone'])
        inputs['emergency_contact_phone'] = re.sub(r'\D', '', inputs['emergency_contact_phone'])
        if len(inputs['phone']) != 10:
            flash('Invalid phone number', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        if len(inputs['emergency_contact_phone']) != 10:
            flash('Invalid emergency contact phone number', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        
        
        for key, value in inputs.items():
            print(key, value)

        # check if email is already in use
        if members.get_membership_by_email(email):
            flash('Email is already in use', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        
        # create membership
        memberships.create_membership(email, inputs)

        session['email'] = email

        return redirect(url_for('account'))
    token = request.args.get('token')
    email = Code.verify_email_token(token)
    if email:
        return render_template('create.html', email=email, inputs={})
    return redirect(url_for('join'))

@app.route('/account')
def account():
    if 'email' in session:
        account = members.get_membership_by_email(session['email'])
        if not account:
            account = [emps.get_emp_by_email(session['email'])]
        return render_template('account.html', members=account)
    return redirect(url_for('login'))

@app.route('/account/<member_id>')
def account_id(member_id):
    if 'email' in session:
        logged_in = emps.get_emp_by_email(session['email'])
        if not logged_in:
            return abort(404)
        account = members.get_membership_by_id(member_id)
        if not account:
            account = [emps.get_emp_by_id(member_id)]
        return render_template('account.html', members=account, admin=True)
    return abort(404)

# login to the admin page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get the username and password
        email = request.form['email']
        password = request.form['password']
        account = members.get_membership_by_email(email)
        if account:
            account = account[0]
        else:
            account = emps.get_emp_by_email(email)
        # check if the username and password are correct
        if account:
            if account.email == email and account.password == password:
                # if correct, redirect to the admin page
                session['email'] = email
                return redirect(url_for('account'))
            else:
                # if incorrect, show an error message
                flash('Invalid username or password', 'error') # this also does not work, no error
    return render_template('login.html')

# logout
@app.route('/logout')
def logout():
    # remove the username from the session
    session.pop('email', None)
    return redirect(url_for('index'))

# checkin
@app.route('/checkin', methods=['GET'])
def checkin():
    if 'email' in session:
        return render_template('checkin.html')
    return redirect(url_for('login'))

@app.route('/checkin', methods=['POST'])
def checkin_post():
    if 'email' in session:
        search = request.form['search']
        if not search:
            return render_template('checkin.html')
        members_found = members.search_member(search)
        return render_template('checkin.html', members_found=members_found)
    return redirect(url_for('login'))

# error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


if __name__ == '__main__':
    app.run(debug=True)