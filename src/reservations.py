from src.models import db, Reservation
import uuid


class Reservation:
    def get_all_reservations(self):
        '''Return all reservations'''
        return Reservation.query.all()
    
    def get_reservation_by_id(self, reservation_id):
        '''Returns reservation by id'''
        return Reservation.query.get(reservation_id)
    
    def get_reservation_by_member_id(self, member_id):
        '''Returns reservation by member_id'''
        return Reservation.query.filter_by(member_id=member_id).first()
    
    def create_reservation(self, member_id, reservation_date, party_size, court_number):
        '''Create reservation'''
        try:
            reservation = Reservation.query.filter_by(member_id=member_id).first()
            if reservation.reservation_date.date() == reservation_date.date():
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
        reservation = Reservation(reservation_id=id, member_id=member_id, reservation_date=reservation_date, party_size=party_size, court_number=court_number)
        db.session.add(reservation)
        db.session.commit()
        return reservation
    
    def update_reservation(self, reservation_id, member_id, reservation_date, party_size, court_number):
        '''Update reservation'''
        reservation = Reservation.query.get(reservation_id)
        reservation.member_id = member_id
        reservation.reservation_date = reservation_date
        reservation.party_size = party_size
        reservation.court_number = court_number
        db.session.commit()
        return reservation
    
    def delete_reservation(self, reservation_id):
        '''Delete reservation'''
        reservation = Reservation.query.get(reservation_id)
        db.session.delete(reservation)
        db.session.commit()
        return reservation
    
    def get_reservations_by_date(self, date):
        '''Returns reservations by date'''
        return Reservation.query.filter(Reservation.reservation_date == date).all()