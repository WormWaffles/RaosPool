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
    return render_template('/index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallary')
def gallary():
    return render_template('gallary.html')

@app.route('/member')
def member():
    return render_template('member.html')

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
            flash('Invalid username or password', 'error')
    return render_template('login.html')

# logout
@app.route('/logout')
def logout():
    # remove the username from the session
    session.pop('username', None)
    return redirect(url_for('index'))

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