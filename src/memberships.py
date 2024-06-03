from src.models import db, Membership
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
        # create uuid for post_id
        id = uuid.uuid1()
        id = id.int
        # make the id 12 digits
        id = str(id)
        id = id[:8]
        id = int(id)
        email = email.lower()
        # create id for member [4 digits i guess]
        membership = Membership(membership_id=id, first_name=inputs['first_name'], last_name=inputs['last_name'], email=email, password=inputs['password'])
        db.session.add(membership)
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