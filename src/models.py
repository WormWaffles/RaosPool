from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Member(db.Model):
    member_id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    profile_image_location = db.Column(db.String(255), nullable=True)

class Emp(db.Model):
    emp_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    admin = db.Column(db.Boolean, nullable=False)