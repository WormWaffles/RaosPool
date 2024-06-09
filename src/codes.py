from src.models import db, Code
import uuid


class Codes:
    def get_all_codes(self):
        '''Returns all codes'''
        return Code.query.all()
    
    def get_code_by_id(self, code_id):
        '''Returns code by id'''
        return Code.query.get(code_id)
    
    def get_code_by_code(self, code):
        '''Returns code by code'''
        code = Code.query.filter_by(code=code).first()
        return code
    
    def get_code_by_email(self, email):
        '''Returns code by email'''
        code = Code.query.filter_by(email=email).first()
        return code
    
    def create_code(self, email):
        '''Creates a code'''
        # check if email is already in use
        if self.get_code_by_email(email):
            self.delete_code(email)
        # create uuid for post_id
        id = uuid.uuid1()
        id = id.int
        # make the id 12 digits
        id = str(id)
        id = id[:8]
        id = int(id)
        code = Code(code_id=id, email=email)
        db.session.add(code)
        db.session.commit()
        return code

    def update_code(self, code_id, email, verification_code):
        '''Updates a code'''
        code = self.get_code_by_id(code_id)
        code.email = email
        code.verification_code = verification_code
        db.session.commit()
        return code
    
    def search_code(self, search):
        '''Query codes id and name ignore case'''
        codes = Code.query.filter(Code.email.ilike(f'%{search}%')).all()
        codes += Code.query.filter(Code.verification_code.ilike(f'%{search}%')).all()
        if codes:
            return codes
        return None
    
    def delete_code(self, code_id):
        '''Deletes a code'''
        code = self.get_code_by_email(code_id)
        db.session.delete(code)
        db.session.commit()
        return code
    
    def clear(self):
        '''Clears all codes'''
        Code.query.delete()
        db.session.commit()
        return True
    
codes = Codes()