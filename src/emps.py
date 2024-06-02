from src.models import db, Emp
from sqlalchemy import text

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
    
    def create_emp(self, id, first_name, last_name, email, password, admin):
        '''Creates an employee'''
        email = email.lower()
        # create id for member [4 digits i guess]
        if admin:
            emp = Emp(emp_id=id, first_name=first_name, last_name=last_name, email=email, password=password, admin=True)
        else:
            emp = Emp(emp_id=id, first_name=first_name, last_name=last_name, email=email, password=password, admin=False)
        db.session.add(emp)
        db.session.commit()
        return emp

    def update_emp(self, emp_id, first_name, last_name, email, password, admin=None):
        '''Updates an employee'''
        emp = self.get_user_by_id(emp_id)
        emp.first_name = first_name
        emp.last_name = last_name
        emp.email = email.lower()
        emp.password = password
        if admin is not None:
            emp.admin = admin
        db.session.commit()
        return emp
    
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
        emp = self.get_user_by_id(emp_id)
        emp.email = "deleted"
        emp.password = None
        db.session.commit()
        return emp
    
    def clear(self):
        '''Clears all employees'''
        Emp.query.delete()
        db.session.commit()

emps = Emps()