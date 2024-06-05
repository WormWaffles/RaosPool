from src.models import db, Membership
from src.members import members
from sqlalchemy import text
import uuid


class Memberships:
    def get_all_memberships(self):
        '''Returns all memberships'''
        return Membership.query.all()
    
    def get_membership_by_id(self, membership_id):
        '''Returns membership by id'''
        return Membership.query.get(membership_id)
    
    def create_membership(self, email, inputs):
        '''Creates a member'''
        email = email.lower()
        membership = Membership(email=email, password=inputs['password'], phone=inputs['phone'], size_of_family=inputs['size_of_family'], street=inputs['street'], city=inputs['city'], state=inputs['state'], zip_code=inputs['zip_code'], membership_type=inputs['membership_type'], referred_by=inputs['referred_by'], emergency_contact_name=inputs['emergency_contact_name'], emergency_contact_phone=inputs['emergency_contact_phone'], last_date_paid=None, active=False)
        db.session.add(membership)
        db.session.commit()
        # create member
        member = members.create_member(membership_id=membership.membership_id, first_name=inputs['fname'], last_name=inputs['lname'], birthday=inputs['dob'], profile_image_location=None)
        db.session.add(member)
        db.session.commit()
        return membership

    def update_membership(self, membership_id, first_name, last_name, email, password, profile_image_location=None):
        '''Updates a member'''
        membership = self.get_membership_by_id(membership_id)
        membership.first_name = first_name
        membership.last_name = last_name
        membership.email = email.lower()
        membership.password = password
        membership.profile_pic = profile_image_location
        db.session.commit()
        return membership
    
    def delete_membership(self, member_id):
        '''Deletes a membership'''
        membership = self.get_member_by_id(member_id)
        db.session.delete(membership)
        db.session.commit()
    
    def clear(self):
        '''Clears all memberships'''
        Membership.query.delete()
        db.session.commit()

memberships = Memberships()