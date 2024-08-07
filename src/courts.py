from src.models import db, Court

class Courts:
    def get_open_courts(self):
        '''Returns the number value in court table'''
        court = Court.query.first()
        if court:
            return court.number
        return 0
    
    def change_open_courts(self, number):
        '''Changes the number value in court table'''
        court = Court.query.first()
        court.number = number
        db.session.commit()
        return court.number
    
    def initialize_courts(self):
        '''Initializes the court table'''
        # check if court table is empty
        court = Court.query.first()
        if court:
            return court.number
        court = Court(number=0)
        db.session.add(court)
        db.session.commit()
        return court.number
    
courts = Courts()