from app import app, db, User, City, Bus, Booking
from werkzeug.security import generate_password_hash
import import_buses_csv

def seed():
    with app.app_context():
        db.create_all()
        
        # Users
        users = [
            ('admin@example.com', 'adminpass', True),
            ('alice@example.com', 'alicepass', False),
            ('bob@example.com', 'bobpass', False)
        ]
        
        for email, pwd, is_adm in users:
            if not User.query.filter_by(email=email).first():
                u = User(email=email, password=generate_password_hash(pwd), is_admin=is_adm)
                db.session.add(u)
        
        db.session.commit()
        print('Seeded users.')

        # Run the CSV importer to get Buses + Cities + Layouts
        import_buses_csv.import_buses()
        
        print('Full Seed Complete.')

if __name__ == '__main__':
    seed()