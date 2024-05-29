from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)

# database connection

# variables

# AWS S3 connection (for member photos)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallary')
def gallary():
    return render_template('gallary.html')

@app.route('/member')
def member():
    return render_template('member.html')

# error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404