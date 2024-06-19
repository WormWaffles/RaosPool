from src.models import db, Membership
from src.members import members
from sqlalchemy import text
import datetime
import uuid


class Memberships:
    def get_all_memberships(self):
        '''Returns all memberships'''
        return Membership.query.all()
    
    def get_membership_by_id(self, membership_id):
        '''Returns membership by id'''
        return Membership.query.get(membership_id)
    
    def get_membership_by_email(self, email):
        '''Returns membership by email'''
        email = email.lower()
        return Membership.query.filter_by(email=email).first()
    
    def get_members_by_membership_id(self, membership_id):
        '''Returns members by membership id'''
        members = db.session.execute(text(f"""
            SELECT member_id, first_name, last_name, birthday
            FROM member
            WHERE membership_id = {membership_id}
            ORDER BY birthday ASC
        """)).fetchall()
        return members
    
    def create_membership(self, email, inputs):
        '''Creates a member'''
        email = email.lower()
        # check if email exists
        if Membership.query.filter_by(email=email).first():
            return False
        membership = Membership(email=email, password=inputs['password'], phone=inputs['phone'], size_of_family=inputs['size_of_family'], street=inputs['street'], city=inputs['city'], state=inputs['state'], zip_code=inputs['zip_code'], membership_type=inputs['membership_type'], referred_by=inputs['referred_by'], emergency_contact_name=inputs['emergency_contact_name'], emergency_contact_phone=inputs['emergency_contact_phone'], last_date_paid=None, active=False, date_joined=datetime.datetime.today())
        db.session.add(membership)
        db.session.commit()
        # create member
        member = members.create_member(membership_id=membership.membership_id, first_name=inputs['fname'], last_name=inputs['lname'], birthday=inputs['dob'], membership_owner=True, profile_image_location=None)
        db.session.add(member)
        db.session.commit()
        return membership

    def update_membership(self, old_email, new_email, inputs):
        '''Updates a member'''
        new_email = new_email.lower()
        membership = Membership.query.filter_by(email=old_email).first()
        membership.email = new_email
        membership.password = inputs['password']
        membership.phone = inputs['phone']
        membership.emergency_contact_name = inputs['emergency_contact_name']
        membership.emergency_contact_phone = inputs['emergency_contact_phone']
        try:
            membership.street = inputs['street']
            membership.city = inputs['city']
            membership.state = inputs['state']
            membership.zip_code = inputs['zip_code']
            membership.active = inputs['active']
            membership.membership_type = inputs['membership_type']
            membership.size_of_family = inputs['size_of_family']
            membership.billing_type = inputs['billing_type'] or None
            membership.last_date_paid = inputs['last_date_paid'] or None
        except:
            pass
        db.session.commit()
        return membership
    
    def update_membership_admin(self, email, inputs):
        '''Update all membership fields'''
        return True

    def reset_password(self, email, password):
        '''Resets password'''
        email = email.lower()
        membership = Membership.query.filter_by(email=email).first()
        membership.password = password
        db.session.commit()
        return True
    
    def search_membership(self, search):
        '''Searches for membership'''
        memberships = db.session.execute(text(f"""
        WITH MemberCheck AS (
            SELECT
                member.member_id,
                member.first_name,
                member.last_name,
                member.birthday,
                member.membership_id,
                EXISTS (
                    SELECT 1
                    FROM checkin
                    WHERE checkin.member_id::INTEGER = member.member_id
                    AND checkin.checkin_date::DATE = CURRENT_DATE
                ) AS has_checked_in_today
            FROM
                member
        )
        SELECT
            membership.membership_id,
            membership.active,
            json_agg(
                json_build_object(
                    'member_id', MemberCheck.member_id,
                    'first_name', MemberCheck.first_name,
                    'last_name', MemberCheck.last_name,
                    'birthday', MemberCheck.birthday,
                    'has_checked_in_today', MemberCheck.has_checked_in_today
                )
            ) AS members
        FROM
            membership
        JOIN
            MemberCheck ON membership.membership_id = MemberCheck.membership_id
        WHERE
            membership.membership_id IN (
                SELECT member.membership_id
                FROM member
                WHERE LOWER(member.first_name) ILIKE LOWER('%{search}%')
                OR LOWER(member.last_name) ILIKE LOWER('%{search}%')
                OR CAST(member.membership_id AS TEXT) ILIKE '%{search}%'
                OR CAST(membership.phone AS TEXT) ILIKE '%{search}%'
            )
        GROUP BY
            membership.membership_id;
        """)).fetchall()
        return memberships
    
    def activate_membership(self, membership_id):
        '''Activates a membership'''
        membership = Membership.query.get(membership_id)
        membership.active = True
        # set paid date to today
        membership.last_date_paid = datetime.datetime.now()
        db.session.commit()
        return membership
    
    def deactivate_membership(self, membership_id):
        '''Deactivates a membership'''
        membership = Membership.query.get(membership_id)
        membership.active = False
        db.session.commit()
        return membership
    
    def fetch_membership_data_from_database(self, page, page_size):
        '''Fetch membership data from database'''
        offset = (page - 1) * page_size
        memberships = db.session.execute(text(f'''
        SELECT * 
        FROM membership 
        ORDER BY 
            CASE 
                WHEN membership.active = false THEN 1 
                WHEN membership.active = true THEN 2 
                ELSE 3 
            END,
            membership.membership_id
        LIMIT {page_size}
        OFFSET {offset};
        '''))
        return memberships
    
    def delete_membership(self, member_id):
        '''Deletes a membership'''
        # get all members ids
        members_to_delete = self.get_members_by_membership_id(member_id)
        # delete all members
        for member in members_to_delete:
            members.delete_member(member.member_id)
        membership = self.get_membership_by_id(member_id)
        db.session.delete(membership)
        db.session.commit()
    
    def clear(self):
        '''Clears all memberships'''
        Membership.query.delete()
        db.session.commit()

memberships = Memberships()