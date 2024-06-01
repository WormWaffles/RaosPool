from src.models import db, Member
from sqlalchemy import text

class Members:
    def get_all_members(self):
        '''Returns all members'''
        return Member.query.all()
    
    def get_member_by_id(self, member_id):
        '''Returns member by id'''
        return Member.query.get(member_id)
    
    def create_member(self, first_name, last_name, email, password, admin=False):
        '''Creates a member'''
        email = email.lower()
        # create id for member [4 digits i guess]
        if admin:
            member = Member(member_id=id, first_name=first_name, last_name=last_name, email=email, password=password, admin=True)
        else:
            member = Member(member_id=id, first_name=first_name, last_name=last_name, email=email, password=password, admin=False)
        db.session.add(member)
        db.session.commit()
        return member

    def update_member(self, member_id, first_name, last_name, email, password, profile_image_location, admin=None):
        '''Updates a member'''
        member = self.get_member_by_id(member_id)
        member.first_name = first_name
        member.last_name = last_name
        member.email = email.lower()
        member.password = password
        member.profile_pic = profile_image_location
        db.session.commit()
        return member
    
    def search_member(self, search):
        '''Query member names and emails ignore case'''
        member = Member.query.filter(Member.member_id.ilike(f'%{search}%')).all()
        member += Member.query.filter(Member.first_name.ilike(f'%{search}%')).all()
        member += Member.query.filter(Member.last_name.ilike(f'%{search}%')).all()
        if member:
            return member
        return None
    
    def delete_member(self, member_id):
        '''Deletes a member'''
        member = self.get_member_by_id(member_id)
        member.email = "deleted"
        member.profile_image_location = None
        member.password = None
        db.session.commit()
        return member
    
    def clear(self):
        '''Clears all members'''
        Member.query.delete()
        db.session.commit()

members = Members()