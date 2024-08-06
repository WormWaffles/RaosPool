from src.models import db, Reservation
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy import text
from flask import jsonify


class Reservations:
    def get_all_reservations(self):
        '''Return all reservations order by reservation_time then court and only return in the future'''
        today = date.today()
        reservations = Reservation.query.filter(Reservation.reservation_date >= datetime.combine(today, datetime.min.time())) \
            .order_by(Reservation.reservation_date, Reservation.reservation_time, Reservation.court_number) \
            .all() 
        return reservations
       
    def get_reservation_by_id(self, reservation_id):
        '''Returns reservation by id'''
        return Reservation.query.get(reservation_id)
    
    def get_reservations_by_member_id(self, member_id):
        '''Returns reservations by member_id sort by reservation_time that are in the future'''
        today = date.today()
        reservations = Reservation.query.filter(Reservation.member_id == str(member_id), Reservation.reservation_date >= datetime.combine(today, datetime.min.time())) \
            .order_by(Reservation.reservation_date, Reservation.reservation_time, Reservation.court_number) \
            .all()
        return reservations
    
    def create_reservation(self, member_id, reservation_date, reservation_time, guest_count, court_number):
        '''Create reservation'''
        try:
            reservation = Reservation.query.filter_by(member_id=member_id).first()
            if reservation.reservation_date.date() == reservation_date.date():
                return None
        except:
            pass
        # create uuid for id
        id = uuid.uuid1()
        id = id.int
        # make the id 12 digits
        id = str(id)
        id = id[:8]
        id = int(id)
        reservation = Reservation(reservation_id=id, member_id=member_id, reservation_date=reservation_date, reservation_time=reservation_time, guest_count=guest_count, court_number=court_number)
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
    
    def cancel_reservation(self, reservation_id):
        '''Cancel reservation'''
        reservation = Reservation.query.get(reservation_id)
        db.session.delete(reservation)
        db.session.commit()
        return reservation
    
    def get_reservations_by_date(self, date):
        '''Returns reservations by date'''
        return Reservation.query.filter(Reservation.reservation_date == date).all()
    
    def check_availability(self, date):
        reservation_date_str = date
        reservation_date = datetime.strptime(reservation_date_str, '%Y-%m-%d').date()

        # Get the number of available courts
        court_count = 2

        # Retrieve all reservations for the given date
        reservations = db.session.query(Reservation).filter_by(reservation_date=reservation_date).all()
        reservations = sorted([(res.reservation_time, res.court_number) for res in reservations])

        # Define the operational hours for the courts
        start_of_day = datetime.combine(reservation_date, datetime.strptime('06:00:00', '%H:%M:%S').time())
        end_of_day = datetime.combine(reservation_date, datetime.strptime('20:00:00', '%H:%M:%S').time())

        available_slots = []
        potential_start = start_of_day

        while potential_start + timedelta(hours=2) <= end_of_day:
            potential_end = potential_start + timedelta(hours=2)
            slot_available = False

            # Check if the potential slot is free on at least one court
            for court_number in range(1, court_count + 1):
                court_reservations = [(res_time, res_court) for res_time, res_court in reservations if res_court == court_number]

                court_slot_available = True
                for res_time, res_court in court_reservations:
                    res_start = res_time
                    res_end = res_time + timedelta(hours=2)

                    if not (potential_end <= res_start or potential_start >= res_end):
                        court_slot_available = False
                        break

                if court_slot_available:
                    slot_available = True
                    break

            if slot_available:
                available_slots.append((potential_start, potential_end))

            potential_start += timedelta(hours=1)  # Increment by 1 hour

        # Format the available slots for output
        available_slots = [(slot[0].strftime('%H:%M'), slot[1].strftime('%H:%M')) for slot in available_slots]

        return available_slots if available_slots else None
    
    def get_available_court_number(self, date, time):
        '''Returns available court number'''
        court_count = 2

        reservation_date_str = date
        reservation_time_str = time

        # Parse the date and time
        reservation_date = datetime.strptime(reservation_date_str, '%Y-%m-%d').date()
        reservation_time = datetime.strptime(reservation_time_str, '%I:%M %p').time()
        reservation_datetime = datetime.combine(reservation_date, reservation_time)

        # Define the operational hours for the courts
        start_of_day = datetime.combine(reservation_date, datetime.strptime('06:00:00', '%H:%M:%S').time())
        end_of_day = datetime.combine(reservation_date, datetime.strptime('20:00:00', '%H:%M:%S').time())

        if reservation_datetime < start_of_day or reservation_datetime > end_of_day:
            return None  # Reservation time is outside operational hours

        # Retrieve all reservations for the given date
        reservations = db.session.query(Reservation).filter_by(reservation_date=reservation_date).all()
        reservations = sorted([(res.reservation_time, res.court_number) for res in reservations])

        # Define the reservation duration
        reservation_duration = timedelta(hours=2)  # Assuming fixed duration of 2 hours for simplicity

        # Check if the potential slot is free on at least one court
        for court_number in range(1, court_count + 1):
            court_reservations = [(res_time, res_court) for res_time, res_court in reservations if res_court == court_number]

            court_slot_available = True
            for res_time, res_court in court_reservations:
                res_start = res_time
                res_end = res_start + reservation_duration

                # Check for overlapping
                if not (reservation_datetime + reservation_duration <= res_start or reservation_datetime >= res_end):
                    court_slot_available = False
                    break

            if court_slot_available:
                return court_number

        return None

reservations = Reservations()