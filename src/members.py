from src.models import db, Member
from sqlalchemy import text

class Members:
    def get_all_members(self):
        '''Returns all members'''
        return Member.query.all()
    
    def get_membership_by_id(self, member_id):
        '''Returns membership by id'''
        member = db.session.execute(text(f"""
            SELECT m.member_id, ms.membership_id, m.first_name, m.last_name, ms.email, m.birthday, m.profile_image_location, ms.password, ms.phone, ms.street, ms.city, ms.state, ms.zip_code, ms.billing_type, ms.membership_type, ms.last_date_paid, ms.size_of_family, ms.active
            FROM member m 
            JOIN membership ms on m.membership_id = ms.membership_id
            WHERE ms.membership_id = {member_id}
        """)).fetchall()
        return member
    
    def get_membership_by_email(self, email):
        '''Returns membership by email'''
        member = db.session.execute(text(f"""
            SELECT m.member_id, ms.membership_id, m.first_name, m.last_name, ms.email, m.birthday, m.profile_image_location, ms.password, ms.phone, ms.street, ms.city, ms.state, ms.zip_code, ms.billing_type, ms.membership_type, ms.last_date_paid, ms.size_of_family, ms.active
            FROM member m 
            JOIN membership ms on m.membership_id = ms.membership_id
            WHERE email = '{email}'
        """)).fetchall()
        return member
    
    def create_member(self, membership_id, first_name, last_name, email, password, profile_image_location=None):
        '''Creates a member'''
        email = email.lower()
        # create id for member [4 digits i guess]
        member = Member(member_id=id, membership_id=membership_id, first_name=first_name, last_name=last_name, email=email, password=password, profile_image_location=None)
        db.session.add(member)
        db.session.commit()
        return member

    def update_member(self, member_id, first_name, last_name, email, password, profile_image_location):
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
        # get members by membership id
        members = []
        if search.isdigit():
            members += db.session.query(Member).filter(Member.membership_id == search).all()
        members += Member.query.filter(Member.first_name.ilike(f'%{search}%')).all()
        members += Member.query.filter(Member.last_name.ilike(f'%{search}%')).all()
        if members:
            return members
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