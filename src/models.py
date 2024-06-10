from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer as Serializer
from dotenv import load_dotenv
import os

db = SQLAlchemy()
secret_key = 'this_is_my_key'

class Membership(db.Model):
    membership_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    street = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    zip_code = db.Column(db.String(80), nullable=False)
    billing_type = db.Column(db.String(80), nullable=False)
    membership_type = db.Column(db.String(80), nullable=False)
    size_of_family = db.Column(db.Integer, nullable=False)
    referred_by = db.Column(db.String(80), nullable=True)
    emergency_contact_name = db.Column(db.String(80), nullable=False)
    emergency_contact_phone = db.Column(db.String(80), nullable=False)
    last_date_paid = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, nullable=False)

    def get_email_token(self):
        s = Serializer(secret_key)
        return s.dumps({'email': self.email})
    
    @staticmethod
    def verify_email_token(token, expires_sec=1800):
        s = Serializer(secret_key)
        try:
            email = s.loads(token, max_age=expires_sec)['email']
        except:
            return None
        return email

class Member(db.Model):
    member_id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    membership_owner = db.Column(db.Boolean, nullable=False)
    profile_image_location = db.Column(db.String(255), nullable=True)

class Emp(db.Model):
    emp_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=True)
    middle_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    us_eligable = db.Column(db.Boolean, nullable=False)
    license = db.Column(db.Boolean, nullable=False)
    street = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    zip_code = db.Column(db.String(80), nullable=False)
    felony = db.Column(db.String(5), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    admin = db.Column(db.Boolean, nullable=False)

class Code(db.Model):
    code_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)

    def get_email_token(self):
        s = Serializer(secret_key)
        return s.dumps({'email': self.email})
    
    @staticmethod
    def verify_email_token(token, expires_sec=1800):
        s = Serializer(secret_key)
        try:
            email = s.loads(token, max_age=expires_sec)['email']
        except:
            return None
        return email
    
class Checkin(db.Model):
    checkin_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, primary_key=True)
    checkin_date = db.Column(db.Date, nullable=False)
