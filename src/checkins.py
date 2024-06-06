from src.models import db, Checkin
import uuid


class Checkins:
    def get_all_checkins(self):
        '''Return all checkins'''
        return Checkins.query.all()
    
    def get_checkin_by_id(self, checkin_id):
        '''Returns checkin by id'''
        return Checkins.query.get(checkin_id)

    def get_checkin_by_member_id(self, member_id):
        '''Returns checkin by member_id'''
        return Checkins.query.filter_by(member_id=member_id).all()
    
    def create_checkin(self, member_id, checkin_date):
        '''Create checkin'''
        # create uuid for id
        id = uuid.uuid1()
        id = id.int
        # make the id 12 digits
        id = str(id)
        id = id[:8]
        id = int(id)
        checkin = Checkins(checkin_id=id, member_id=member_id, checkin_date=checkin_date)
        db.session.add(checkin)
        db.session.commit()
        return checkin
    
    def delete_emp(self, checkin_id):
        '''Deletes a checkin'''
        checkin = self.get_checkin_by_id(checkin_id)
        db.session.delete(checkin)
        db.session.commit()
        return True
    
    def clear(self):
        '''Clears all checkins'''
        Checkins.query.delete()
        db.session.commit()

checkins = Checkins()