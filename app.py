from flask import Flask, render_template, request, redirect, url_for, flash, session, g, abort, send_file
import requests
import os
from src.models import db, Code
from src.members import members
from src.emps import emps
from src.codes import codes
from src.memberships import memberships
from src.checkins import checkins
from src.reservations import reservations
from src.courts import courts
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask import jsonify
import datetime
import uuid
import re
import csv
import json
import stripe
import time




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
app.config['SQLALCHEMY_ECHO'] = False # set to True to see SQL queries
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max upload size

db.init_app(app)

# stripe connection
app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = app.config['STRIPE_SECRET_KEY']


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
bcrypt = Bcrypt(app)

images = []
def get_images():
    global images
    files = os.listdir('static/images/events')
    images = [image for image in files if not image.startswith('.')]
    image_paths = [os.path.join('static/images/events', image) for image in images]
    sorted_image_paths = sorted(image_paths, key=os.path.getmtime, reverse=True)
    sorted_images = [os.path.basename(image) for image in sorted_image_paths]
    images = sorted_images

get_images()


# AWS S3 connection (for member photos)

# check if the user is logged in
@app.before_request
def before_request():
    g.user = None
    if 'email' in session:
        g.user = session['email']

def send_email(email, subject, body):
    msg = Message(subject, sender=os.getenv('DEFAULT_SENDER'), recipients=[email])
    msg.body = f'{body}'
    mail.send(msg)


@app.route('/')
def index():
    return render_template('/index.html', g=g, home=True, image=images[0])

@app.route('/events')
def events():
    get_images()
    if 'email' in session:
        try:
            if emps.get_emp_by_email(session['email']).admin:
                return render_template('events.html', events=True, images=images, admin=True)
        except:
            pass
    return render_template('events.html', events=True, images=images, admin=False)

@app.route('/pickleball')
def pickleball():
    if 'email' in session:
        try:
            member = memberships.get_membership_by_email(session['email'])
            emp = emps.get_emp_by_email(session['email'])
            if member:
                if member.active:
                    return render_template('pickleball.html', pickleball=True, access=True, days_in_advance=3)
            elif emp.active:
                return render_template('pickleball.html', pickleball=True, access=True)
        except:
            pass
    return render_template('pickleball.html', pickleball=True)

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
        if not re.fullmatch(regex, email):
            flash('Invalid email', 'error')
            return render_template('contact.html', contact=True)
        
        message = f'''Name: {first_name} {last_name}
Email: {email}

Inquiry: {message}'''

        send_email(os.getenv('CONTACT_RECEIVER'), f'Inquiry from {first_name} {last_name}', message)
        return render_template('confirmation.html', message='Thanks for your feedback, your message has been sent', sub_message='We will get back to you as soon as possible')

    return render_template('contact.html', contact=True)

@app.route('/join', methods=['GET', 'POST'])
def join():
    if 'email' in session:
        return redirect('/account')
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
        if emps.get_emp_by_email(email):
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

NOTE: This link expires in 30 minutes.

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
            inputs['agree'] = request.form.get('agree')
            if not inputs['agree']:
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
        # if date is less than 18 years ago
        dob = datetime.datetime.strptime(inputs['dob'], '%Y-%m-%d')
        if datetime.datetime.now().year - dob.year < 18:
            flash('You must be at least 18 years old or older to create a membership', 'error')
            return render_template('create.html', email=email, inputs=inputs)

        # check if email is already in use
        if members.get_membership_by_email(email):
            flash('Email is already in use', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        # check if employee has that email
        if emps.get_emp_by_email(email):
            flash('Email is already in use', 'error')
            return render_template('create.html', email=email, inputs=inputs)
        
        # encrypt password
        inputs['password'] = Bcrypt().generate_password_hash(inputs['password']).decode()

        # create membership
        memberships.create_membership(email, inputs)

        try:
            logged_in = emps.get_emp_by_email(session['email'])
            if logged_in.admin:
                pass
        except:
            session['email'] = email

        send_email(os.getenv('DEFAULT_SENDER'), "New member has joined!", f'{inputs["fname"]} {inputs["lname"]} has joined Rao\'s!\n\nEmail: {email}\nPhone: {inputs["phone"]}\nDOB: {inputs["dob"]}\nAddress: {inputs["street"]}, {inputs["city"]}, {inputs["state"]} {inputs["zip_code"]}\nMembership type: {inputs["membership_type"]}\nReferred by: {inputs["referred_by"]}\nEmergency contact: {inputs["emergency_contact_name"]}, {inputs["emergency_contact_phone"]}')
        member_id = members.get_membership_by_email(email)[0].membership_id
        return render_template('confirmation.html', message = f'Your membership has been created!', sub_message=f'Member # {member_id}. Click below to finish your account.', button='account', link='/account?user_id=' + str(member_id))
    try:
        logged_in = emps.get_emp_by_email(session['email'])
        if logged_in.admin:
            return render_template('create.html', email='', inputs={})
    except:
        pass
    token = request.args.get('token')
    email = Code.verify_email_token(token)
    if email:
        return render_template('create.html', email=email, inputs={})
    flash('Link expired, enter email to receive a new link.', 'error')
    return redirect(url_for('join'))

@app.route('/create/member', methods=['GET', 'POST'])
def create_member():
    if 'email' in session:
        membership_id = request.args.get('membership_id')
        try:
            # Retrieve the logged-in user's employee details
            employee = emps.get_emp_by_email(session['email'])
            
            # If the employee is an admin, allow further actions
            if employee and employee.admin:
                pass  # Admins are allowed to proceed
            # For non-admin users, check if the user_id matches the logged-in user's ID
            else:
                membership = members.get_membership_by_email(session['email'])
                if membership and str(membership[0].membership_id) == str(membership_id):
                    pass
                else:
                    return abort(404)
        except:
            # Optionally log the exception or handle specific exception types
            return abort(404)
        if request.method == 'POST':
            # if membership is full
            account = members.get_membership_by_id(membership_id)
            # check if logged in is admin
            logged_in = emps.get_emp_by_email(session['email'])
            if logged_in and logged_in.admin:
                if len(account) >= account[0].size_of_family:
                    flash('Membership is full', 'error')
                    return redirect(url_for('account', membership_id=membership_id))
            # get form info
            inputs = {}
            try:
                inputs['fname'] = request.form['fname']
                inputs['lname'] = request.form['lname']
                inputs['dob'] = request.form['dob']
            except:
                flash('Please fill out all fields', 'error')
                return render_template('create_member.html', inputs=inputs)
            for key, value in inputs.items():
                if value == '':
                    flash('Please fill out all fields', 'error')
                    return render_template('create_member.html', inputs=inputs)
            # create member
            member = members.create_member(membership_id=membership_id, first_name=inputs['fname'], last_name=inputs['lname'], birthday=inputs['dob'], profile_image_location=None)
            db.session.add(member)
            db.session.commit()
            return redirect(url_for('account', membership_id=membership_id))
        return render_template('create_member.html', membership_id=membership_id, inputs={})
    return redirect(url_for('login'))

@app.route('/account')
def account():
    if 'email' not in session:
        return redirect(url_for('login'))
    membership_id = request.args.get('membership_id')
    emp_id = request.args.get('employee_id')

    logged_in = emps.get_emp_by_email(session['email'])
    try:
        if str(emp_id) == str(logged_in.emp_id):
            return redirect(url_for('account'))
    except:
        pass
    try:
        if logged_in.admin:
            if membership_id:
                return render_template('account.html', members=members.get_membership_by_id(membership_id), can_add_member=True, edit=True, emp=True, admin=True)
            if emp_id:
                return render_template('account.html', members=[emps.get_emp_by_id(emp_id)], can_add_member=False, edit=True, emp=True, admin=True)
            return render_template('account.html', members=[emps.get_emp_by_email(session['email'])], can_add_member=True, edit=True, emp=True, admin=True, my_account=True)
    except:
        pass
    emp = emps.get_emp_by_email(session['email'])
    if emp:
        return render_template('account.html', members=[emps.get_emp_by_email(session['email'])], can_add_member=False, edit=True, emp=True, admin=False)
    member = members.get_membership_by_email(session['email'])
    try:
        if str(membership_id) == str(member[0].membership_id):
                return redirect(url_for('account'))
    except:
        pass
    if member:
        account = members.get_membership_by_email(session['email'])
        can_add_member = len(account) < account[0].size_of_family
        return render_template('account.html', members=account, can_add_member=can_add_member, edit=False, admin=False)
    return abort(404)

@app.route('/account/edit', methods=['GET', 'POST'])
def edit_account():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_id = request.args.get('user_id')
    try:
        employee = emps.get_emp_by_email(session['email'])
        if employee and employee.admin:
            pass  # Admins are allowed to proceed
        else:
            return abort(404)
    except:
        return abort(404)
    emp = emps.get_emp_by_id(user_id)
    if not emp:
        return abort(404)
    
    if request.method == 'POST':
        # get form info
        inputs = {}
        try:
            inputs['position'] = request.form['position']
            inputs['first_name'] = request.form['first_name']
            inputs['middle_name'] = request.form['middle_name']
            inputs['last_name'] = request.form['last_name']
            old_email = request.form['old_email']
            new_email = request.form['email']
            inputs['phone'] = request.form['phone']
            inputs['street'] = request.form['street']
            inputs['city'] = request.form['city']
            inputs['state'] = request.form['state']
            inputs['zip_code'] = request.form['zip_code']
            inputs['dob'] = request.form['dob']
            inputs['us_eligable'] = request.form.get('us_eligable') == 'on'
            inputs['license'] = request.form.get('license') == 'on'
            inputs['felony'] = request.form['felony']
        except:
            flash('Please fill out all fields', 'error')
            return redirect(request.referrer)
        for key, value in inputs.items():
            if value == '':
                flash('Please fill out all fields', 'error')
                return redirect(request.referrer)
        try:
            inputs['active'] = request.form.get('active') == 'on'
            inputs['admin'] = request.form.get('admin') == 'on'
            inputs['password'] = Bcrypt().generate_password_hash(request.form['password']).decode()
            if not inputs['password']:
                inputs['password'] = emp.password
        except:
            inputs['password'] = emp.password
        if inputs['zip_code'].isdigit() == False:
            flash('Invalid zip code', 'error')
            return redirect(request.referrer)
        if len(inputs['zip_code']) != 5:
            flash('Invalid zip code', 'error')
            return redirect(request.referrer)
        # if new email is taken
        if new_email != old_email:
            if members.get_membership_by_email(new_email) or emps.get_emp_by_email(new_email):
                flash('Email in use', 'error')
                return redirect(request.referrer)
        if not re.fullmatch(regex, new_email):
            flash('Invalid email', 'error')
            return redirect(request.referrer)
        if len(inputs['password']) < 8:
            flash('Password must be at least 8 characters', 'error')
            return redirect(request.referrer)
        inputs['phone'] = re.sub(r'\D', '', inputs['phone'])
        if len(inputs['phone']) != 10:
            flash('Invalid phone number', 'error')
            return redirect(request.referrer)
        if inputs['felony'] not in ['yes', 'no']:
            flash('Invalid felony response', 'error')
            return redirect(request.referrer)
        if inputs['position'] not in ['Management', 'Lifeguard', 'Snack Bar']:
            flash('Invalid position', 'error')
            return redirect(request.referrer)

        # create membership
        emps.update_emp(old_email, new_email, inputs)
        if session['email'] == old_email:
            session['email'] = new_email
        return redirect(url_for('account', employee_id=user_id))
    inputs = {
        'position': emp.position,
        'first_name': emp.first_name,
        'middle_name': emp.middle_name,
        'last_name': emp.last_name,
        'phone': emp.phone,
        'street': emp.street,
        'city': emp.city,
        'state': emp.state,
        'zip_code': emp.zip_code,
        'dob': emp.birthday,
        'us_eligable': emp.us_eligable,
        'license': emp.license,
        'felony': emp.felony
    }
    try:
        inputs['active'] = emp.active
        inputs['admin'] = emp.admin
    except:
        pass
    if emps.get_emp_by_email(session['email']).admin:
        return render_template('edit_emp.html', account=emp, email=emp.email, inputs=inputs, admin=True)
    return render_template('edit_emp.html', account=emp, email=emp.email, inputs=inputs)
                   
# login to the admin page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get the username and password
        email = request.form['email']
        password = request.form['password']
        if email == '' or password == '':
            flash('Please fill out all fields', 'error')
            return render_template('login.html')
        account = members.get_membership_by_email(email)
        if account:
            account = account[0]
        else:
            account = emps.get_emp_by_email(email)
        # check if the username and password are correct
        if account:
            if account.email == email and bcrypt.check_password_hash(account.password, password):
                # if correct, redirect to the admin page
                session['email'] = email
                return redirect(url_for('account'))
            else:
                flash('Invalid email or password.', 'error')
                return render_template('login.html')
        else:
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
    return render_template('login.html')

# reset password
@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form['email']
        account = members.get_membership_by_email(email)
        if account:
            account = account[0]
        else:
            account = emps.get_emp_by_email(email)
        if account:
            code = codes.create_code(email=email)
            token = Code.get_email_token(code)
            message = f'''
Click the link to reset your password:
{url_for("reset_password", token=token, _external=True)}

NOTE: This link expires in 30 minutes.

If you did not make this request, ignore this email.
            '''
            send_email(email, "Rao's: reset password", message)
            return render_template('confirmation.html', message = f'Thanks! We sent an email to {email}', sub_message='Please check your email to reset your password')
        flash('Email not associated with an account.', 'error')
    return render_template('reset.html')

@app.route('/reset/password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.args.get('email')
        password = request.form['password']
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('reset_password.html')
        account = memberships.get_membership_by_email(email)
        new_password = bcrypt.generate_password_hash(password).decode()
        if not account:
            account = emps.get_emp_by_email(email)
            emps.reset_password(email, new_password)
            return redirect(url_for('login'))
        if account:
            memberships.reset_password(email, new_password)
            return redirect(url_for('login'))
        flash('Invalid email', 'error')
    else:
        token = request.args.get('token')
        email = Code.verify_email_token(token)
        if email:
            return render_template('reset_password.html', email=email)
    return redirect(url_for('reset'))

# delete member
@app.route('/member/delete/<member_id>')
def delete_member(member_id):
    if 'email' in session:
        logged_in = emps.get_emp_by_email(session['email'])
        if logged_in.admin:
            members.delete_member(member_id)
        # return back to where you were
        return redirect(request.referrer)
    return abort(404)

# logout
@app.route('/logout')
def logout():
    # remove the username from the session
    session.pop('email', None)
    return redirect(url_for('index'))

# checkin
@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if 'email' in session and emps.get_emp_by_email(session['email']).active == False:
        return redirect(url_for('login'))
    stats = checkins.get_all_stats()
    if request.method == 'POST':
        search = request.form['search']
        if not search:
            return render_template('checkin.html', stats=stats)
        memberships_found = memberships.search_membership(search)
        return render_template('checkin.html', memberships_found=memberships_found, stats=stats)
    return render_template('checkin.html', stats=stats)

@app.route('/checkin/log')
def checkin_log():
    if 'email' in session and emps.get_emp_by_email(session['email']).active == True:
        membership_id = request.args.get('membership_id')
        date = datetime.datetime.now()
        if membership_id:
            members = memberships.get_members_by_membership_id(membership_id)
            for member in members:
                checkins.create_checkin(str(member.member_id), date)
            return 'nothing'
        member_id = request.args.get('member_id')
        if member_id:
            checkins.create_checkin(member_id, date)
            return 'nothing'
    return 'nothing'

@app.route('/checkin/stats')
def checkin_stats():
    if 'email' in session and emps.get_emp_by_email(session['email']).active == True:
        if not emps.get_emp_by_email(session['email']):
            return abort(404)
        return render_template('checkin_stats.html')
    return redirect(url_for('login'))

@app.route('/checkin/get')
def get_checkin_data():
    # Retrieve page number and page size from query parameters
    page = request.args.get('page', type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    # Fetch check-in data from the database (you need to implement this)
    # You might need to adjust the code based on your database structure
    checkin_data = checkins.fetch_checkin_data_from_database(page, page_size)

    # Convert check-in data to a list of dictionaries with specific columns
    data = []
    for checkin in checkin_data:
        checkin_dict = {
            'membership_id': checkin.membership_id,
            'first_name': checkin.first_name,
            'last_name': checkin.last_name,
            'date': checkin.checkin_date
        }
        data.append(checkin_dict)

    # Return check-in data as JSON
    return jsonify(data)

# Employee pages *******
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        # get form info
        inputs = {}
        try:
            inputs['position'] = request.form['position']
            inputs['first_name'] = request.form['first_name']
            inputs['middle_name'] = request.form['middle_name']
            inputs['last_name'] = request.form['last_name']
            email = request.form['email']
            inputs['password'] = request.form['password']
            inputs['phone'] = request.form['phone']
            inputs['dob'] = request.form['dob'] # not working
            if request.form.get('us_eligable'):
                inputs['us_eligable'] = True
            else:
                inputs['us_eligable'] = False
            if request.form.get('license'):
                inputs['license'] = True
            else:
                inputs['license'] = False
            inputs['street'] = request.form['street']
            inputs['city'] = request.form['city']
            inputs['state'] = request.form['state']
            inputs['zip_code'] = request.form['zip_code']
            inputs['felony'] = request.form['felony']
        except:
            flash('Please fill out all fields', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        for key, value in inputs.items():
            if value == '':
                flash('Please fill out all fields', 'error')
                return render_template('apply.html', email=email, inputs=inputs)
        if inputs['zip_code'].isdigit() == False:
            flash('Invalid zip code', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        if len(inputs['zip_code']) != 5:
            flash('Invalid zip code', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        if not re.fullmatch(regex, email):
            flash('Invalid email', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        if len(inputs['password']) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        inputs['phone'] = re.sub(r'\D', '', inputs['phone'])
        if len(inputs['phone']) != 10:
            flash('Invalid phone number', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        if inputs['felony'] not in ['yes', 'no']:
            flash('Invalid felony response', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        if inputs['position'] not in ['Management', 'Lifeguard', 'Snack Bar']:
                flash('Invalid position', 'error')
                return redirect(request.referrer)
        
        # check if email is already in use
        if members.get_membership_by_email(email):
            flash('Email is already in use', 'error')
            return render_template('apply.html', email=email, inputs=inputs)
        # check if employee has that email
        if emps.get_emp_by_email(email):
            flash('Email is already in use', 'error')
            return render_template('apply.html', email=email, inputs=inputs)

        # encrypt password
        inputs['password'] = Bcrypt().generate_password_hash(inputs['password']).decode()
        # create employee
        emps.create_emp(email, inputs)
        session['email'] = email

        # send email to owner
        send_email(os.getenv('DEFAULT_SENDER'), "New employee has applied!", f'{inputs["first_name"]} {inputs["last_name"]} has applied to work at Rao\'s!\n\nEmail: {email}\nPhone: {inputs["phone"]}\nDOB: {inputs["dob"]}\nAddress: {inputs["street"]}, {inputs["city"]}, {inputs["state"]} {inputs["zip_code"]}\nUS Eligable: {inputs["us_eligable"]}\nLicense: {inputs["license"]}\nFelony: {inputs["felony"]}')

        return redirect(url_for('account'))
    return render_template('apply.html', inputs={})

@app.route('/applications')
def applications():
    if 'email' not in session:
        return redirect(url_for('login'))
    if not emps.get_emp_by_email(session['email']).admin:
        return abort(404)
    return render_template('applications.html', mem_len=len(memberships.get_all_memberships()), emp_len=len(emps.get_all_emps()))

@app.route('/applications/get/memberships')
def get_applications():
    # Retrieve page number and page size from query parameters
    page = request.args.get('page', type=int)
    page_size = request.args.get('pageSize', 8, type=int)
    
    mem_applications = memberships.fetch_membership_data_from_database(page, page_size)

    # Convert check-in data to a list of dictionaries with specific columns
    mem_data = []
    for mem in mem_applications:
        mem_dict = {
            'membership_id': mem.membership_id,
            'joined_date': mem.date_joined,
            'email': mem.email,
            'active': mem.active,
        }
        mem_data.append(mem_dict)
    
    # Return check-in data as JSON
    return jsonify(mem_data)

@app.route('/applications/get/employees')
def get_employee_applications():
    # Retrieve page number and page size from query parameters
    page = request.args.get('page', type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    
    emp_applications = emps.fetch_emp_data_from_database(page, page_size)

    # Convert check-in data to a list of dictionaries with specific columns
    emp_data = []
    for emp in emp_applications:
        emp_dict = {
            'emp_id': emp.emp_id,
            'email': emp.email,
            'active': emp.active,
        }
        emp_data.append(emp_dict)
    
    # Return check-in data as JSON
    return jsonify(emp_data)

@app.route('/account/delete')
def delete_account():
    if not emps.get_emp_by_email(session['email']).admin:
        return abort(404)
    delete_id = request.args.get('delete_id')
    to_delete = memberships.get_membership_by_id(delete_id)
    if to_delete:
        memberships.delete_membership(delete_id)
    to_delete = emps.get_emp_by_id(delete_id)
    if to_delete:
        emps.delete_emp(delete_id)
    return redirect(url_for('applications'))

@app.route('/account/activate')
def activate_account():
    if not emps.get_emp_by_email(session['email']).admin:
        return abort(404)
    activate_id = request.args.get('activate_id')
    to_activate = memberships.get_membership_by_id(activate_id)
    if to_activate:
        memberships.activate_membership(activate_id)
    to_activate = emps.get_emp_by_id(activate_id)
    if to_activate:
        emps.activate_emp(activate_id)
    return redirect(request.referrer)

@app.route('/account/deactivate')
def deactivate_account():
    if not emps.get_emp_by_email(session['email']).admin:
        return abort(404)
    deactivate_id = request.args.get('deactivate_id')
    to_deactivate = memberships.get_membership_by_id(deactivate_id)
    if to_deactivate:
        memberships.deactivate_membership(deactivate_id)
    to_deactivate = emps.get_emp_by_id(deactivate_id)
    if to_deactivate:
        emps.deactivate_emp(deactivate_id)
    return redirect(request.referrer)

@app.route('/policies')
def policies():
    return render_template('policies.html')

@app.route('/download_data', methods=['GET'])
def download_data():
    if not 'email' in session and emps.get_emp_by_email(session['email']).admin:
        abort(404)

    # delete existing csv file
    for file in os.listdir():
        if file.endswith('.csv'):
            os.remove(file)
    mem_data = memberships.get_data()
    csv_filename = f'{datetime.datetime.now().strftime("%Y-%m-%d")}_membership_data.csv'

    with open(csv_filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['ID', 'Email', 'Phone', 'Street', 'City', 'State', 'Zip', 'Type', 'Size', 'Ref', 'EmerName', 'EmerPhone', 'BillType', 'LastPaid', 'Active', 'Members'])  # Write headers

        for membership in mem_data:
            members_json = json.dumps(membership.members)
            csv_writer.writerow([
                membership.membership_id, membership.email, membership.phone, membership.street,
                membership.city, membership.state, membership.zip_code, membership.membership_type,
                membership.size_of_family, membership.referred_by, membership.emergency_contact_name,
                membership.emergency_contact_phone, membership.billing_type, membership.last_date_paid,
                membership.active, members_json
            ])    
    return send_file(csv_filename, as_attachment=True)

@app.route('/applications/search', methods=['GET'])
def search_application():
    if not 'email' in session and emps.get_emp_by_email(session['email']).admin:
        abort(404)
    search = request.args.get('search')
    if not search:
        return redirect(url_for('applications'))
    memberships_found = memberships.search_membership(search)

    # make the data json friendly
    data = []
    for member in memberships_found:
        members_dict = {
            'membership_id': member.membership_id,
            'joined_date': member.date_joined,
            'email': member.email,
            'active': member.active,
        }
        data.append(members_dict)

    return jsonify(data)

# add event photo route
@app.route('/event/add', methods=['GET', 'POST'])
def add_event_photo():
    if 'email' in session and emps.get_emp_by_email(session['email']).admin:
        if request.method == 'GET':
            return render_template('add_event_photo.html')
        if request.method == 'POST':
            file = request.files['file']
            # add file to events folder
            if file:
                # Generate a unique filename (e.g., using UUID)
                file_extension = os.path.splitext(file.filename)[1]
                unique_filename = str(uuid.uuid4())[:8] + file_extension
                upload_folder = 'static/images/events'
                os.makedirs(upload_folder, exist_ok=True)  # Ensure the directory exists
                # Save the file to the specified directory
                file.save(os.path.join(upload_folder, unique_filename))
                get_images()
                return redirect(url_for('events'))
            flash('No file selected', 'error')
            return render_template('add_event_photo.html')
    return abort(404)

# delete event photo route
@app.route('/event/delete', methods=['PUT'])
def delete_event_photo():
    if 'email' in session and emps.get_emp_by_email(session['email']).admin:
        image_id = request.args.get('image_id')
        if not image_id:
            return abort(404)
        # delete the photo from the events folder
        os.remove(f'static/images/events/{image_id}')
        get_images()        
        return 'nothing'
    return abort(404)


# Pickleball routes
@app.route('/pickleball/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        # get form info
        member_id = request.form['membership_id']
        date = request.form['date']
        time = request.form['time']
        guest_count = request.form['guest_count']

        if not member_id:
            member_id = 'Guest'
        if not date or not time or not guest_count:
            abort(404)
        if guest_count.isdigit() == False:
            flash('Invalid party size', 'error')
            return render_template('reserve.html', date=date, time=time, membership_id=member_id)
        if int(guest_count) < 0 or int(guest_count) > 4:
            flash('Invalid party size', 'error')
            return render_template('reserve.html', date=date, time=time, membership_id=member_id)
        
        # get the court number
        court_number = reservations.get_available_court_number(date, time)
        if not court_number:
            flash('No courts available at that time', 'error')
            return redirect(url_for('pickleball'))
        
        # turn date and time into timestamp
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        time = datetime.datetime.strptime(time, '%I:%M %p').time()
        time = datetime.datetime.combine(date, time)

        # make new reservation
        code = reservations.create_reservation(member_id, date, time, guest_count, court_number)
        if code == None:
            flash('Error creating reservations, try again.', 'error')
            return redirect(url_for('pickleball'))
        
        if not code:
            flash('You can only reserve one court per day.', 'error')
            return redirect(url_for('pickleball'))
        
        # check if emp is admin, if so do not charge
        try:
            is_emp = emps.get_emp_by_email(session['email']).admin
        except:
            is_emp = False

        # reservation created, now get payment if guest
        if int(guest_count) > 0 and not is_emp:
            # if guest, change price_id
            if member_id == 'Guest':
                price_id = 'price_1PjnH7FWhayxBXWqXY9vRCJw'
            else:
                price_id = 'price_1PjnGFFWhayxBXWqpaw1bEry'
            try:
                user_email = session.get('email')  # Get the email if it exists, otherwise it will be None

                metadata = {
                    'reservation_id': code
                }

                # Add email to metadata only if it's available
                if user_email:
                    metadata['email'] = user_email

                checkout_session = stripe.checkout.Session.create(
                    line_items=[
                        {
                            # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                            'price': price_id,
                            'quantity': guest_count,
                        },
                    ],
                    mode='payment',
                    success_url=url_for('confirmation', _external=True, 
                        message=f'Processing Payment for Court #{court_number}', 
                        sub_message='You will receive a confirmation email.') + '&session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=url_for('pickleball', _external=True),
                    automatic_tax={'enabled': True},
                    metadata=metadata
                )

            except Exception as e:
                print(str(e))
                return abort(400)

            print(checkout_session)
            return redirect(checkout_session.url, code=303)
        else:
            success = reservations.confirm_reservation(code)
            if not success:
                flash('Error confirming reservation', 'error')
                return redirect(url_for('pickleball'))
            else:
                send_email(session['email'], 'Reservation Confirmed', 'Your reservation has been confirmed. We look forward to seeing you!')

        return render_template('confirmation.html', message=f'Court #{court_number} Reserved', sub_message='You should receive an email confirmation shortly.')
    date = request.args.get('date')
    time = request.args.get('time')
    # convert time to 12 hour format
    time = datetime.datetime.strptime(time, '%H:%M').strftime('%I:%M %p')
    # remove leading 0
    if time[0] == '0':
        time = time[1:]
    # if the user is logged in send the member number as well
    if 'email' in session:
        member = memberships.get_membership_by_email(session['email'])
        if member:
            return render_template('reserve.html', date=date, time=time, membership_id=member.membership_id)
    return render_template('reserve.html', date=date, time=time)

@app.route('/confirmation')
def confirmation():
    session_id = request.args.get('session_id')
    print(session_id)
    message = request.args.get('message', 'Default Message')
    sub_message = request.args.get('sub_message', 'Default Sub-Message')
    return render_template('confirmation.html', message=message, sub_message=sub_message)


@app.route('/getmember/<int:member_id>', methods=['GET'])
def get_member(member_id):
    # get member info
    member = members.get_membership_by_id(member_id)
    # if membership is active
    if member and member[0].active:
        # turn member into dictionary
        member_info = {
            'membership_id': member[0].membership_id,
            'name': f'{member[0].first_name} {member[0].last_name}'
        }
        if member:
            print(member_info)
            return jsonify(member_info)
    return {}

@app.route('/account/reservations', methods=['GET'])
def account_reservations():
    if 'email' in session:
        member = members.get_membership_by_email(session['email'])
        if member:
            my_reservations = reservations.get_reservations_by_member_id(member[0].membership_id)
            print(my_reservations)
            return render_template('account_reservations.html', reservations=my_reservations)
    return redirect(url_for('login'))

@app.route('/reservations', methods=['GET'])
def reservations_page():
    if 'email' in session:
        if emps.get_emp_by_email(session['email']).admin:
            all_reservations = reservations.get_all_reservations()
            court_number = courts.get_open_courts()
            return render_template('reservations.html', reservations=all_reservations, open_courts=court_number)
    return abort(404)

@app.route('/reservations/cancel/<reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    if 'email' in session:
        if emps.get_emp_by_email(session['email']).admin:
            print(reservation_id)
            reservations.cancel_reservation(reservation_id)
            return 'nothing'
    return abort(404)

# api route to get open court times
@app.route('/api/pickleball/times', methods=['GET'])
def get_times():
    # get the date
    date = request.args.get('date')
    # get the times that are reserved
    available_times = reservations.check_availability(date)
    # turn times into dict with true or false
    times = {}
    try:
        for time in available_times:
            times[time[0]] = True
    except:
        return jsonify({})
    # return times as json
    return jsonify(times)

@app.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    if request.content_length > 1024 * 1024:
        print('Request too large')
        abort(400)

    sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        print('Invalid payload')
        return {}, 400
    except stripe.error.SignatureVerificationError as e:
        print('Invalid signature')
        return {}, 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        reservation_id = session['metadata']['reservation_id']
        try:
            user_email = session['metadata']['email']
        except:
            user_email = None
        
        # Attempt to confirm the reservation
        success = reservations.confirm_reservation(reservation_id)
        
        if not success:
            print('Error confirming reservation')
            # 1. Log the failure for investigation
            app.logger.error(f"Failed to confirm reservation {reservation_id}")
            
            # 2. Optionally, retry confirmation a few times
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries and not success:
                retry_count += 1
                time.sleep(2)  # delay between retries
                success = reservations.confirm_reservation(reservation_id)
            
            if not success:
                # 3. Attempt to process a refund
                try:
                    refund = stripe.Refund.create(payment_intent=session['payment_intent'])
                    if refund.status != 'succeeded':
                        app.logger.error(f"Refund for payment_intent {session['payment_intent']} failed")
                        # Optionally retry refund or flag for manual intervention
                except Exception as e:
                    app.logger.error(f"Error creating refund: {e}")
                    # Notify admin or take further action
                    send_email(os.getenv('DEFAULT_SENDER'), "Error processing refund", f"Error processing refund for reservation {reservation_id}: {e}")
                    
                # 4. Update internal reservation status
                reservation = reservations.get_reservation_by_id(reservation_id)
                if reservation:
                    # remove the reservation
                    db.session.delete(reservation)
                    db.session.commit()

                # Send an email or notification to the user about the failed reservation
                if user_email:
                    send_email(user_email, 'Reservation Failed', 'Your reservation could not be confirmed. Please contact support for assistance.')
        else:
            if user_email:
                send_email(user_email, 'Reservation Confirmed', 'Your reservation has been confirmed. We look forward to seeing you!')
    return {}

# api route to get and set open courts
@app.route('/api/pickleball/courts', methods=['GET', 'POST'])
def get_courts():
    # initialize the courts
    if not courts.get_open_courts():
        courts.initialize_courts()
    if request.method == 'POST':
        # get court number
        court_number = request.args.get('court_number')
        print(court_number)
        courts.change_open_courts(court_number)
        return 'nothing'
    # get the open courts
    open_courts = courts.get_open_courts()
    return jsonify(open_courts)

# error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


if __name__ == '__main__':
    app.run(debug=True)