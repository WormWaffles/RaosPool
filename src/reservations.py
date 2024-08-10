from src.models import db, Reservation
from src.courts import courts
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy import text, and_


class Reservations:
    def get_all_reservations(self):
        '''Return all reservations order by reservation_time then court and only return in the future'''
        today = date.today()
        reservations = Reservation.query.filter(
            and_(
                Reservation.reservation_date >= datetime.combine(today, datetime.min.time()),
                Reservation.confirmed == True
            )
        ).order_by(
            Reservation.reservation_date,
            Reservation.reservation_time,
            Reservation.court_number
        ).all()
        return reservations
       
    def get_reservation_by_id(self, reservation_id):
        '''Returns reservation by id'''
        return Reservation.query.get(reservation_id)
    
    def get_reservations_by_member_id(self, member_id):
        '''Returns reservations by member_id sort by reservation_time that are in the future'''
        today = date.today()
        reservations = Reservation.query.filter(
            and_(
                Reservation.member_id == str(member_id),
                Reservation.reservation_date >= datetime.combine(today, datetime.min.time()),
                Reservation.confirmed == True
            )
        ).order_by(
            Reservation.reservation_date,
            Reservation.reservation_time,
            Reservation.court_number
        ).all()
        return reservations
    
    def create_reservation(self, member_id, reservation_date, reservation_time, guest_count, court_number):
        '''Create reservation'''
        # lock table
        db.session.execute(text('LOCK TABLE reservation IN ACCESS EXCLUSIVE MODE'))
        
        try:
            # Convert reservation_date to string
            strg = reservation_date.strftime('%Y-%m-%d')
            formatted_reservation_time = reservation_time.strftime('%H:%M')

            # Check if reservation time is available
            available_times = self.check_availability(strg)
            available_times_flat = [time for interval in available_times for time in interval]

            if formatted_reservation_time not in available_times_flat:
                print(f"Reservation time '{reservation_time}' is not available.")
                print(f"Available times: {available_times_flat}")
                return None
            
            
            if member_id != 'Guest':
                reservations = Reservation.query.filter_by(member_id=str(member_id)).all()
                for reservation in reservations:
                    if reservation.reservation_date == reservation_date.date() and reservation.confirmed == True:
                        return False
            
            # create uuid for id
            id = uuid.uuid1()
            id = id.int
            # make the id 12 digits
            id = str(id)
            id = id[:8]
            id = int(id)
            
            # create and add the reservation
            reservation = Reservation(reservation_id=id, member_id=member_id, reservation_date=reservation_date, reservation_time=reservation_time, guest_count=guest_count, court_number=court_number, confirmed=False)
            db.session.add(reservation)
            db.session.commit()
            
            return id
        
        except Exception as e:
            # if an exception occurs, rollback the transaction
            db.session.rollback()
            raise e
        
        finally:
            # regardless of what happens, close the session
            db.session.close()
    
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
        court_count = courts.get_open_courts()

        # Retrieve all confirmed reservations for the given date
        reservations = db.session.query(Reservation).filter(
            Reservation.reservation_date == reservation_date,
            Reservation.confirmed == True
        ).all()
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
        court_count = courts.get_open_courts()

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
        reservations = db.session.query(Reservation).filter(
            Reservation.reservation_date == reservation_date,
            Reservation.confirmed == True
        ).all()
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

    def confirm_reservation(self, reservation_id):
        '''Confirm reservation with table-level locking to avoid race conditions'''
        try:
            # Start a transaction
            if not db.session.is_active:
                db.session.begin()

            # Lock the table to prevent concurrent access
            db.session.execute(text('LOCK TABLE reservation IN ACCESS EXCLUSIVE MODE'))

            # Lock the row for update
            reservation = db.session.query(Reservation).filter_by(reservation_id=reservation_id).first()

            if not reservation:
                print(f'Reservation with ID {reservation_id} not found.')
                db.session.rollback()  # Rollback the transaction as reservation is not found
                return False  # Reservation not found

            # Check for conflicting confirmed reservations
            conflicting_reservations = db.session.query(Reservation).filter(
                Reservation.court_number == reservation.court_number,
                Reservation.reservation_date == reservation.reservation_date,
                Reservation.reservation_time == reservation.reservation_time,
                Reservation.confirmed == True
            ).count()

            if conflicting_reservations > 0:
                print(f'Conflicting reservations: {conflicting_reservations}')
                db.session.rollback()  # Rollback the transaction as there is a conflict
                return False  # Conflict found

            # No conflicts, proceed to confirm
            reservation.confirmed = True
            db.session.commit()
            return True

        except Exception as e:
            print(e)
            db.session.rollback()  # Ensure rollback on exception
            return False  # Indicate failure in case of exception
        finally:
            db.session.close()


reservations = Reservations()