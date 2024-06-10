from flask import Flask, render_template, request, redirect, url_for, flash, session, g, abort
import requests
import os
from src.models import db, Member, Emp, Code, Membership
from src.members import members
from src.emps import emps
from src.codes import codes
from src.memberships import memberships
from src.checkins import checkins
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask import jsonify
import datetime
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
app.config['SQLALCHEMY_ECHO'] = False # set to True to see SQL queries
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
bcrypt = Bcrypt(app)


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

        session['email'] = email

        send_email(os.getenv('DEFAULT_SENDER'), "New member has joined!", f'{inputs["fname"]} {inputs["lname"]} has joined Rao\'s!\n\nEmail: {email}\nPhone: {inputs["phone"]}\nDOB: {inputs["dob"]}\nAddress: {inputs["street"]}, {inputs["city"]}, {inputs["state"]} {inputs["zip_code"]}\nMembership type: {inputs["membership_type"]}\nReferred by: {inputs["referred_by"]}\nEmergency contact: {inputs["emergency_contact_name"]}, {inputs["emergency_contact_phone"]}')

        return redirect(url_for('account'))
    token = request.args.get('token')
    email = Code.verify_email_token(token)
    if email:
        return render_template('create.html', email=email, inputs={})
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
                return abort(404)
        except:
            # Optionally log the exception or handle specific exception types
            return abort(404)
        if request.method == 'POST':
            # if membership is full
            account = members.get_membership_by_id(membership_id)
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

    edit = False
    try:
        edit = emps.get_emp_by_email(session['email']).admin
    except:
        edit = True

    try:
        if membership_id:
            account = members.get_membership_by_id(membership_id)
        elif emp_id:
            account = emps.get_emp_by_id(emp_id)
        else:
            account = members.get_membership_by_email(session['email'])
    except:
        pass

    try:
        if membership_id and str(members.get_membership_by_email(session['email'])[0].membership_id) != membership_id:
            return abort(404)
    except:
        pass

    if account.__class__ == list:
        if len(account) > 0:
            if not account:
                return redirect(url_for('logout'))
            
            can_add_member = len(account) < account[0].size_of_family
            return render_template('account.html', members=account, can_add_member=can_add_member, edit=True)

    if account:
        return render_template('account.html', members=[account], can_add_member=False, emp=True, edit=edit)

    account = [emps.get_emp_by_email(session['email'])]
    return render_template('account.html', members=account, can_add_member=True, emp=True, edit=edit)

@app.route('/account/edit', methods=['GET', 'POST'])
def edit_account():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_id = request.args.get('user_id')
    try:
        # Retrieve the logged-in user's employee details
        employee = emps.get_emp_by_email(session['email'])
        
        # If the employee is an admin, allow further actions
        if employee and employee.admin:
            pass  # Admins are allowed to proceed
        # For non-admin users, check if the user_id matches the logged-in user's ID
        else:
            membership = members.get_membership_by_email(session['email'])
            if membership and str(membership[0].membership_id) == str(user_id):
                pass
            else:
                employee = emps.get_emp_by_email(session['email'])
                if employee and str(employee.emp_id) == str(user_id):
                    pass
                else:
                    return abort(404)
    except:
        # Optionally log the exception or handle specific exception types
        return abort(404)
    if len(user_id) < 5:
        membership_id = user_id
        logged_in = emps.get_emp_by_email(session['email'])
        if not logged_in and not members.get_membership_by_email(session['email']):
            return abort(404)
        account = members.get_membership_by_id(membership_id)
        if not account:
            account = emps.get_emp_by_id(id)
            if not account:
                return abort(404)
        if account[0].membership_id != int(membership_id):
            return abort(404)
        account = account[0]
        if request.method == 'POST':
            # get form info
            inputs = {}
            try:
                email = request.form['email']
                inputs['phone'] = request.form['phone']
                inputs['street'] = request.form['street']
                inputs['city'] = request.form['city']
                inputs['state'] = request.form['state']
                inputs['zip_code'] = request.form['zip']
                inputs['emergency_contact_name'] = request.form['emergency_contact_name']
                inputs['emergency_contact_phone'] = request.form['emergency_contact_phone']
            except:
                flash('Please fill out all fields', 'error')
                return redirect(request.referrer)
            for key, value in inputs.items():
                if value == '':
                    flash('Please fill out all fields', 'error')
                    return redirect(request.referrer)
            try:
                inputs['active'] = request.form.get('active') == 'on'
                inputs['membership_type'] = request.form['membership_type']
                inputs['size_of_family'] = request.form['size_of_family']
                inputs['billing_type'] = request.form['billing_type']
                inputs['last_date_paid'] = request.form['last_date_paid']
                inputs['password'] = Bcrypt().generate_password_hash(request.form['password']).decode()
                if not inputs['password']:
                    inputs['password'] = account.password
            except:
                inputs['password'] = account.password
            if inputs['zip_code'].isdigit() == False:
                flash('Invalid zip code', 'error')
                return redirect(request.referrer)
            if len(inputs['zip_code']) != 5:
                flash('Invalid zip code', 'error')
                return redirect(request.referrer)
            if not re.fullmatch(regex, email):
                flash('Invalid email', 'error')
                return redirect(request.referrer)
            if len(inputs['password']) < 8:
                flash('Password must be at least 8 characters', 'error')
                return redirect(request.referrer)
            inputs['phone'] = re.sub(r'\D', '', inputs['phone'])
            inputs['emergency_contact_phone'] = re.sub(r'\D', '', inputs['emergency_contact_phone'])
            if len(inputs['phone']) != 10:
                flash('Invalid phone number', 'error')
                return redirect(request.referrer)
            if len(inputs['emergency_contact_phone']) != 10:
                flash('Invalid emergency contact phone number', 'error')
                return redirect(request.referrer)

            # create membership
            memberships.update_membership(email, inputs)
            return redirect(url_for('account', membership_id=membership_id))
        membership = account
        inputs = {
            'phone': membership.phone,
            'street': membership.street,
            'city': membership.city,
            'state': membership.state,
            'zip_code': membership.zip_code,
            'emergency_contact_name': membership.emergency_contact_name,
            'emergency_contact_phone': membership.emergency_contact_phone
        }
        try:
            if logged_in.emp_id:
                inputs['active'] = membership.active
                inputs['birthday'] = membership.birthday
                inputs['size_of_family'] = membership.size_of_family
                inputs['billing_type'] = membership.billing_type
                inputs['last_date_paid'] = membership.last_date_paid
                inputs['membership_type'] = membership.membership_type
                inputs['last_date_paid'] = membership.last_date_paid
        except:
            pass

        return render_template('edit_membership.html', account=account, email=membership.email, inputs=inputs)
    else:
        emp = emps.get_emp_by_id(user_id)
        if not emp:
            return abort(404)
        
        if request.method == 'POST':
            # get form info
            inputs = {}
            try:
                inputs['first_name'] = request.form['first_name']
                inputs['middle_name'] = request.form['middle_name']
                inputs['last_name'] = request.form['last_name']
                email = request.form['email']
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
            if not re.fullmatch(regex, email):
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

            # create membership
            emps.update_emp(email, inputs)
            return redirect(url_for('account', employee_id=user_id))
        inputs = {
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
                # if incorrect, show an error message
                flash('Invalid username or password.', 'error') # this also does not work, no error
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

If you did not make this request, ignore this email.
            '''
            send_email(email, "Rao's: reset password", message)
            return render_template('confirmation.html', message = f'Thanks! We sent an email to {email}', sub_message='Please check your email to reset your password')
        flash('Invalid email', 'error')
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
@app.route('/account/delete/<member_id>')
def delete_member(member_id):
    if 'email' in session:
        logged_in = emps.get_emp_by_email(session['email'])
        if not logged_in:
            logged_in = members.get_membership_by_email(session['email'])
            if not logged_in:
                return abort(404)
            if member_id in logged_in:
                members.delete_member(member_id)
        else:
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
            return render_template('checkin.html')
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
            return render_template('apply.html', inputs=inputs)
        for key, value in inputs.items():
            if value == '':
                flash('Please fill out all fields', 'error')
                return render_template('apply.html', inputs=inputs)
        if inputs['zip_code'].isdigit() == False:
            flash('Invalid zip code', 'error')
            return render_template('apply.html', inputs=inputs)
        if len(inputs['zip_code']) != 5:
            flash('Invalid zip code', 'error')
            return render_template('apply.html', inputs=inputs)
        if not re.fullmatch(regex, email):
            flash('Invalid email', 'error')
            return render_template('apply.html', inputs=inputs)
        if len(inputs['password']) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('apply.html', inputs=inputs)
        inputs['phone'] = re.sub(r'\D', '', inputs['phone'])
        if len(inputs['phone']) != 10:
            flash('Invalid phone number', 'error')
            return render_template('apply.html', inputs=inputs)
        if inputs['felony'] not in ['yes', 'no']:
            flash('Invalid felony response', 'error')
            return render_template('apply.html', inputs=inputs)
        
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
    recent_memberships = memberships.get_recent_memberships()
    recent_emps = emps.get_recent_emps()
    return render_template('applications.html', recent_emps=recent_emps, recent_memberships=recent_memberships)


# error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404


if __name__ == '__main__':
    app.run()
