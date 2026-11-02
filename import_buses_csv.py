import csv, os
import math
from app import app, db, City, Bus, Booking

CSV_FILE = os.path.join(os.path.dirname(__file__), 'buses.csv')

def ensure_city(name):
    city = City.query.filter_by(name=name).first()
    if not city:
        city = City(name=name)
        db.session.add(city)
        db.session.commit()
    return city

def generate_layout(total_seats):
    """
    Generates a standard 2x2 layout JSON based on total seats.
    """
    seats_per_row = 4
    rows = math.ceil(total_seats / seats_per_row)
    
    return {
        "total_rows": rows,
        "seats_per_row": seats_per_row,
        "aisle_after": 2, # Aisle after 2nd seat (2+2 layout)
        "col_labels": ["A", "B", "C", "D"]
    }

def import_buses():
    if not os.path.exists(CSV_FILE):
        print('buses.csv not found')
        return
        
    print("Importing buses with Optimized JSON Layouts...")
    
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('name','').strip()
            if not name:
                continue
                
            if Bus.query.filter_by(name=name).first():
                print('Skipping (already exists):', name)
                continue
                
            source = ensure_city(row.get('source','').strip()) if row.get('source') else None
            dest = ensure_city(row.get('dest','').strip()) if row.get('dest') else None
            price = float(row.get('price') or 0)
            seats_count = int(row.get('seats') or 40)
            
            # Generate the dynamic layout
            layout = generate_layout(seats_count)
            
            # Default amenities
            amenities = {"wifi": True, "usb": True, "water_bottle": False}
            if "AC" in name or "Deluxe" in name:
                amenities["ac"] = True
                amenities["water_bottle"] = True

            bus = Bus(
                name=name, 
                source_city_id=source.id if source else None, 
                dest_city_id=dest.id if dest else None, 
                base_price=price, 
                layout_config=layout, # Storing JSON
                amenities=amenities   # Storing JSON
            )
            
            db.session.add(bus)
            print(f'Imported {name} with {seats_count} seats (Dynamic Layout)')
            
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        # Clean old tables if they differ significantly or just append
        db.create_all()
        import_buses()