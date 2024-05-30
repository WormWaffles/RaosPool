from src.models import db, User
from sqlalchemy import text

class Users:
    def get_all_users(self):
        '''Returns all users'''
        return User.query.all()
    
    def get_user_by_id(self, user_id):
        '''Returns user by id'''
        return User.query.get(user_id)
    
    def create_user(self, first_name, last_name, email, password, admin=False):
        '''Creates a user'''
        email = email.lower()
        # create id for member [4 digits i guess]
        if admin:
            user = User(user_id=id, first_name=first_name, last_name=last_name, email=email, password=password, admin=True)
        else:
            user = User(user_id=id, first_name=first_name, last_name=last_name, email=email, password=password, admin=False)
        db.session.add(user)
        db.session.commit()
        return user

    def update_user(self, user_id, first_name, last_name, email, password, profile_image_location, admin=None):
        '''Updates a user'''
        user = self.get_user_by_id(user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email.lower()
        user.password = password
        user.profile_pic = profile_image_location
        db.session.commit()
        return user
    
    def search_user(self, search):
        '''Query user names and emails ignore case'''
        user = User.query.filter(User.user_id.ilike(f'%{search}%')).all()
        user += User.query.filter(User.first_name.ilike(f'%{search}%')).all()
        user += User.query.filter(User.last_name.ilike(f'%{search}%')).all()
        if user:
            return user
        return None
    
    def delete_user(self, user_id):
        '''Deletes a user'''
        user = self.get_user_by_id(user_id)
        user.email = "deleted"
        user.profile_image_location = None
        user.password = None
        db.session.commit()
        return user
    
    def clear(self):
        '''Clears all users'''
        User.query.delete()
        db.session.commit()

users = Users()