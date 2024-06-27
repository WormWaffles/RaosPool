from src.models import db, Checkin
from sqlalchemy import func, extract, cast, Date, text
import uuid
import datetime


class Checkins:
    def get_all_checkins(self):
        '''Return all checkins'''
        return Checkin.query.all()
    
    def get_checkin_by_id(self, checkin_id):
        '''Returns checkin by id'''
        return Checkin.query.get(checkin_id)
    
    def fetch_checkin_data_from_database(self, page, page_size):
        '''Fetch checkin data from database'''
        offset = (page - 1) * page_size
        checkins = db.session.execute(text(f'''
        SELECT
            checkin.checkin_id,
            checkin.member_id,
            checkin.checkin_date,
            member.membership_id,
            member.first_name,
            member.last_name
        FROM
            checkin
        JOIN
            member ON checkin.member_id::INTEGER = member.member_id
        ORDER BY
            checkin.checkin_date DESC
        LIMIT 10
        OFFSET {offset};
        '''))
        return checkins

    def get_checkin_by_member_id(self, member_id):
        '''Returns checkin by member_id'''
        return Checkin.query.filter_by(member_id=member_id).first()
    
    def create_checkin(self, member_id, checkin_date):
        '''Create checkin'''
        try:
            checkin = Checkin.query.filter_by(member_id=member_id).first()
            if checkin.checkin_date.date() == checkin_date.date():
                return 'nothing'
        except:
            pass
        # create uuid for id
        id = uuid.uuid1()
        id = id.int
        # make the id 12 digits
        id = str(id)
        id = id[:8]
        id = int(id)
        checkin = Checkin(checkin_id=id, member_id=member_id, checkin_date=checkin_date)
        db.session.add(checkin)
        db.session.commit()
        return checkin
    
    def get_all_stats(self):
        '''Returns all stats'''
        # get checkins with a date withing the last 24 hours
        last_24_hours = datetime.datetime.now() - datetime.timedelta(days=1)
        checkins_today = Checkin.query.filter(Checkin.checkin_date > last_24_hours).all()
        # Get today's date
        today_date = datetime.date.today()
        checkins_month = Checkin.query.filter(
            extract('month', cast(Checkin.checkin_date, Date)) == today_date.month
        ).all()

        # Get all checkins for this year (without time)
        checkins_year = Checkin.query.filter(
            extract('year', cast(Checkin.checkin_date, Date)) == today_date.year
        ).all()
        stats = {
            'checkins_today': len(checkins_today),
            'checkins_month': len(checkins_month),
            'checkins_year': len(checkins_year)
        }
        return stats
    
    def delete_emp(self, checkin_id):
        '''Deletes a checkin'''
        checkin = self.get_checkin_by_id(checkin_id)
        db.session.delete(checkin)
        db.session.commit()
        return True
    
    def clear(self):
        '''Clears all checkins'''
        Checkin.query.delete()
        db.session.commit()

checkins = Checkins()