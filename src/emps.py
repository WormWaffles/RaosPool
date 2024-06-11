from src.models import db, Emp
from sqlalchemy import text
import uuid


class Emps:
    def get_all_emps(self):
        '''Returns all emplpyees'''
        return Emp.query.all()
    
    def get_emp_by_id(self, emp_id):
        '''Returns employee by id'''
        return Emp.query.get(emp_id)
    
    def get_emp_by_email(self, email):
        '''Returns employee by email'''
        emp = Emp.query.filter_by(email=email).first()
        return emp
    
    def create_emp(self, email, inputs):
        '''Creates an employee'''
        # create uuid for post_id
        id = uuid.uuid1()
        id = id.int
        # make the id 12 digits
        id = str(id)
        id = id[:8]
        id = int(id)
        email = email.lower()
        # create id for member [4 digits i guess]
        emp = Emp(emp_id=id, first_name=inputs['first_name'], middle_name=inputs['middle_name'], last_name=inputs['last_name'], email=email, password=inputs['password'], phone=inputs['phone'], birthday=inputs['dob'], us_eligable=inputs['us_eligable'], license=inputs['license'], street=inputs['street'], city=inputs['city'], state=inputs['state'], zip_code=inputs['zip_code'], felony=inputs['felony'], admin=False, active=False)
        db.session.add(emp)
        db.session.commit()
        return emp

    def update_emp(self, email, inputs):
        '''Updates an employee'''
        email = email.lower()
        emp = Emp.query.filter_by(email=email).first()
        emp.first_name = inputs['first_name']
        emp.middle_name = inputs['middle_name']
        emp.last_name = inputs['last_name']
        emp.email = email
        emp.password = inputs['password']
        emp.phone = inputs['phone']
        emp.us_eligable = inputs['us_eligable']
        emp.license = inputs['license']
        emp.street = inputs['street']
        emp.city = inputs['city']
        emp.state = inputs['state']
        emp.zip_code = inputs['zip_code']
        emp.felony = inputs['felony']
        emp.active = inputs['active']
        emp.admin = inputs['admin']
        db.session.commit()        
        return emp
    
    def reset_password(self, email, password):
        '''Resets an employee's password'''
        emp = self.get_emp_by_email(email)
        emp.password = password
        db.session.commit()
        return emp
    
    def get_recent_emps(self):
        '''Returns the most recent applications from emps and members'''
        recent_apps = db.session.execute(text(f"""
            SELECT * FROM emp limit 30;
        """)).fetchall()
        return recent_apps

    def search_emp(self, search):
        '''Query employees id and name ignore case'''
        emps = Emp.query.filter(Emp.emp_id.ilike(f'%{search}%')).all()
        emps += Emp.query.filter(Emp.first_name.ilike(f'%{search}%')).all()
        emps += Emp.query.filter(Emp.last_name.ilike(f'%{search}%')).all()
        if emps:
            return emps
        return None
    
    def delete_emp(self, emp_id):
        '''Deletes an employee'''
        emp = self.get_emp_by_id(emp_id)
        db.session.delete(emp)
        db.session.commit()
        return emp
    
    def clear(self):
        '''Clears all employees'''
        Emp.query.delete()
        db.session.commit()

emps = Emps()