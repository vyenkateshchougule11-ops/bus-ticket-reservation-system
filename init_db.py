from app import app, db, User, City
from werkzeug.security import generate_password_hash

def seed():
    with app.app_context():
        db.create_all()
        
        # Seed Admin
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(email='admin@example.com', password=generate_password_hash('adminpass'), is_admin=True)
            db.session.add(admin)
            
        # Seed Cities
        for n in ['Mumbai','Pune','Bangalore','Hyderabad','Jaipur','Jodhpur','Mangalore','Goa']:
            if not City.query.filter_by(name=n).first():
                db.session.add(City(name=n))
                
        db.session.commit()
        print('DB initialized and seeded with Users and Cities.')

if __name__ == '__main__':
    seed()