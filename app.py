from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import requests

app = Flask(__name__)

# database connection

# variables
app.secret_key = "secret key"

# AWS S3 connection (for member photos)

# check if the user is logged in
@app.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = session['username']

@app.route('/')
def index():
    return render_template('/index.html', g=g, home=True)

@app.route('/events')
def events():
    return render_template('events.html', events=True)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html', pricing=True)

@app.route('/contact')
def contact():
    return render_template('contact.html', contact=True)

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        # get a lot of infor
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        phone = request.form['phone']
        option = request.form.get('option', '')
        print(fname, lname, email, phone) # save to database [todo] ************
        print(option)
        if fname:
            # send email to the email address [todo] ************
            return render_template('confirmation.html', name=fname)
        else:
            flash('Invalid email or code', 'error') # this does not work, no error shown
    return render_template('join.html')

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')


@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/admin')
def admin():
    if 'username' in session:
        return render_template('admin.html')
    return redirect(url_for('login'))

# login to the admin page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get the username and password
        username = request.form['username']
        password = request.form['password']
        # check if the username and password are correct
        if username == 'admin' and password == 'admin':
            # if correct, redirect to the admin page
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            # if incorrect, show an error message
            flash('Invalid username or password', 'error') # this also does not work, no error
    return render_template('login.html')

# logout
@app.route('/logout')
def logout():
    # remove the username from the session
    session.pop('username', None)
    return redirect(url_for('index'))

# checkin
@app.route('/checkin', methods=['GET'])
def checkin():
    if 'username' in session:
        return render_template('checkin.html')
    return redirect(url_for('login'))

@app.route('/checkin', methods=['POST'])
def checkin_post():
    if 'username' in session:
        search = request.form['search']
        print(search) # search for member based on search info TODO******
        members_found = [search]
        return render_template('checkin.html', members_found=members_found)
    return redirect(url_for('login'))

# add member
@app.route('/addmember', methods=['POST'])
def addmember():
    if 'username' in session:
        # get the member details
        email = request.form['email']
        # send email to the email address [todo] ************

        # redirect to the admin page
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

# error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404