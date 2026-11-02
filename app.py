import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import pdfkit
import shutil
from flask import make_response

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-this')
app.config['UPLOAD_FOLDER'] = 'static/bus_images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Configuration (MySQL Recommended)
DB_URL = os.environ.get('DB_URL') or 'sqlite:///redbus.db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==========================================
# 1. DATABASE MODELS
# ==========================================

class Agency(db.Model):
    __tablename__ = 'agencies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    buses = db.relationship('Bus', backref='owner_agency', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    agency_id = db.Column(db.Integer, db.ForeignKey('agencies.id'), nullable=True)
    
    # ADD THIS LINE:
    # This lets us do 'current_user.agency.name' in the template
    agency = db.relationship('Agency', backref='agency_users', lazy=True)

    @property
    def is_admin(self): return self.role == 'admin'
    @property
    def is_agency(self): return self.role == 'agency'

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Bus(db.Model):
    __tablename__ = 'buses'
    id = db.Column(db.Integer, primary_key=True)
    agency_id = db.Column(db.Integer, db.ForeignKey('agencies.id'))
    name = db.Column(db.String(200), nullable=False)
    bus_type = db.Column(db.String(50)) # Sleeper/Seater
    layout_type = db.Column(db.String(20)) # 2+2, 2+1, 1+1
    base_price = db.Column(db.Float, default=0.0)
    source_city_id = db.Column(db.Integer, db.ForeignKey('cities.id'))
    dest_city_id = db.Column(db.Integer, db.ForeignKey('cities.id'))

   
    
    # Scheduling & Amenities
    departure_date_time = db.Column(db.DateTime, nullable=False)
    travel_duration_hours = db.Column(db.Float, nullable=False)
    arrival_date_time = db.Column(db.DateTime)
    is_ac = db.Column(db.Boolean, default=False)
    has_food = db.Column(db.Boolean, default=False)
    has_water = db.Column(db.Boolean, default=False)
    has_snacks = db.Column(db.Boolean, default=False)
    images = db.Column(db.Text) # Comma-separated filenames
    source = db.relationship('City', foreign_keys=[source_city_id])
    destination = db.relationship('City', foreign_keys=[dest_city_id])
class Station(db.Model):
    __tablename__ = 'stations'
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id', ondelete='CASCADE'))
    name = db.Column(db.String(200))
    stop_order = db.Column(db.Integer)
    arrival_time = db.Column(db.String(10)) 
    price_adjustment = db.Column(db.Float, default=0.0)

# class Seat(db.Model):
#     __tablename__ = 'seats'  # Add this if not already there
#     id = db.Column(db.Integer, primary_key=True)
#     bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
#     id = db.Column(db.Integer, primary_key=True)
#     bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
#     seat_no = db.Column(db.String(10), nullable=False)
#     row = db.Column(db.Integer, nullable=False)
#     column = db.Column(db.Integer, nullable=False) # 1 to 5
#     deck = db.Column(db.String(10), default='Lower') # 'Lower' or 'Upper'
#     is_available = db.Column(db.Boolean, default=True)


class Seat(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    seat_no = db.Column(db.String(10), nullable=False)
    row = db.Column(db.Integer, nullable=False)
    column = db.Column(db.Integer, nullable=False)
    deck = db.Column(db.String(10), default='Lower')
    is_available = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, nullable=False) # <--- ADD THIS COLUMN

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)

    # These must match the columns we just added
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    passenger_gender = db.Column(db.String(10), nullable=False)
    final_price = db.Column(db.Float, nullable=False)
    
    booking_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships to help pull data for the PDF
    user = db.relationship('User', backref='bookings')
    bus = db.relationship('Bus', backref='bookings')
    seat = db.relationship('Seat', backref='bookings')

# ==========================================
# 2. CORE LOGIC & ROUTES
# ==========================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            email=email, 
            password=generate_password_hash(password),
            role='user'  # Default role for normal travelers
        )
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# **********************************

@app.route('/booking-success/<int:booking_id>')
@login_required
def booking_success(booking_id):
    # Fetch the main booking to get the bus and transaction details
    main_booking = Booking.query.get_or_404(booking_id)
    
    # If you want to show all passengers booked in this specific session, 
    # we filter by user, bus, and the timestamp of the main booking.
    related_bookings = Booking.query.filter_by(
        user_id=current_user.id, 
        bus_id=main_booking.bus_id,
        booking_date=main_booking.booking_date
    ).all()

    return render_template('booking_success.html', 
                           main_booking=main_booking, 
                           bookings=related_bookings)

# ******************************************************************************

@app.route('/register-agency', methods=['GET', 'POST'])
def register_agency():
    if request.method == 'POST':
        email = request.form.get('email')
        company = request.form.get('company_name')
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register_agency'))
        
        new_agency = Agency(name=company)
        db.session.add(new_agency)
        db.session.flush()
        
        user = User(email=email, password=generate_password_hash(request.form.get('password')), 
                    role='agency', agency_id=new_agency.id)
        db.session.add(user)
        db.session.commit()
        flash('Agency Registered! Please Login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_agency.html')

@app.route('/agency/dashboard')
@login_required
def agency_dashboard():
    if not current_user.is_agency: return redirect(url_for('index'))
    buses = Bus.query.filter_by(agency_id=current_user.agency_id).all()
    cities = City.query.all()
    return render_template('agency_dashboard.html', buses=buses, cities=cities)


def generate_seats(bus):
    # Determine decks: Sleepers use two decks, Seaters use one
    levels = ['Lower', 'Upper'] if bus.bus_type == 'Sleeper' else ['Lower']

    for deck in levels:
        # Determine number of rows: 6 for Sleeper (to get 18 per deck), 11 for Seater
        total_rows = 6 if bus.bus_type == 'Sleeper' else 11
        
        for r in range(1, total_rows + 1): 
            
            # --- DYNAMIC PRICING LOGIC ---
            if bus.bus_type == 'Sleeper':
                # Rows 3 and 4 are premium for the 6-row sleeper layout
                seat_price = bus.base_price + 100 if 3 <= r <= 4 else bus.base_price
            else:
                # Original Seater logic: Rows 4-7 premium, Row 10+ discount
                if 4 <= r <= 7:
                    seat_price = bus.base_price + 50
                elif r >= 10:
                    seat_price = bus.base_price - 20
                else:
                    seat_price = bus.base_price
            
            # --- LAYOUT LOGIC ---
            if bus.bus_type == 'Sleeper':
                # 2+1 Sleeper Layout: Columns 1, 3, and 4 (Column 2 is the aisle)
                # This applies identically to both Upper and Lower decks
                active_cols = [1, 3, 4]
            else:
                # Original Seater 2+2 Layout Logic
                if r == 11:
                    active_cols = [1, 2, 3, 4, 5] # Full back row
                else:
                    active_cols = [1, 2, 4, 5] # Standard 2+2

            for c in active_cols:
                # Generate Seat Numbers
                if bus.bus_type == 'Sleeper':
                    prefix = "L" if deck == "Lower" else "U"
                    seat_no = f"{prefix}{r}{chr(64+c)}" # e.g., L1A, U1A
                else:
                    seat_no = f"{r}{chr(64+c)}" # e.g., 1A
                
                new_seat = Seat(
                    bus_id=bus.id, 
                    seat_no=seat_no, 
                    row=r, 
                    column=c, 
                    deck=deck,
                    price=seat_price
                )
                db.session.add(new_seat)
    
    db.session.commit()

@app.route('/agency/add-bus', methods=['POST'])
@login_required
def add_bus():
    # 1. Prepare data first (timing and images)
    dept_str = request.form.get('departure_time')
    duration = float(request.form.get('duration'))
    dept_dt = datetime.strptime(dept_str, '%Y-%m-%dT%H:%M')
    arr_dt = dept_dt + timedelta(hours=duration)

    imgs = []
    for i in range(1, 5):
        f = request.files.get(f'image_{i}')
        if f and f.filename != '':
            fname = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            imgs.append(fname)

    # 2. ASSIGN new_bus HERE (This fixes the UnboundLocalError)
    new_bus = Bus(
        name=request.form.get('name'),
        agency_id=current_user.agency_id,
        bus_type=request.form.get('bus_type'),
        layout_type=request.form.get('layout_type'),
        departure_date_time=dept_dt,
        travel_duration_hours=duration,
        arrival_date_time=arr_dt,
        base_price=float(request.form.get('base_price')),
        source_city_id=request.form.get('source_id'),
        dest_city_id=request.form.get('dest_id'),
        is_ac='is_ac' in request.form,
        has_food='has_food' in request.form,
        has_water='has_water' in request.form,
        has_snacks='has_snacks' in request.form,
        images=",".join(imgs) # Use the imgs list prepared above
    )

    db.session.add(new_bus)
    db.session.commit()
    # ... rest of seat generation code
    # === ADD THIS LINE HERE ===
    generate_seats(new_bus) 
    # ==========================
    return redirect(url_for('agency_dashboard'))

# @app.route('/calculate-dynamic-price', methods=['POST'])
# def calculate_dynamic_price():
#     data = request.get_json()
#     bus = Bus.query.get(data['bus_id'])
#     b_adj = Station.query.get(data['board_id']).price_adjustment if data.get('board_id') else 0
#     a_adj = Station.query.get(data['alight_id']).price_adjustment if data.get('alight_id') else 0
#     return jsonify({'success': True, 'final_price': round(bus.base_price + b_adj + a_adj, 2)})



# -----------------Add Sarch Option----------------------
@app.route('/search', methods=['POST'])
def search():
    source_id = request.form.get('source')
    dest_id = request.form.get('dest')
    
    if not source_id or not dest_id:
        flash('Please select both source and destination', 'warning')
        return redirect(url_for('index'))
    
    # Query buses and join with Agency for display
    buses = Bus.query.filter_by(source_city_id=source_id, dest_city_id=dest_id).all()
    
    source_city = City.query.get(source_id)
    dest_city = City.query.get(dest_id)
    
    return render_template('search.html', 
                           buses=buses, 
                           source=source_city, 
                           dest=dest_city)

# -------------------------22-12-25------------------------------
# import pdfkit

# # @login_required
# def download_ticket(booking_id):
#     booking = Booking.query.get_or_404(booking_id)
#     bus = Bus.query.get(booking.bus_id)
#     board = Station.query.get(booking.board_station_id)
#     alight = Station.query.get(booking.alight_station_id)
#     seat = Seat.query.get(booking.seat_id)

#     # Render HTML for the ticket
#     rendered = render_template('ticket_pdf.html', 
#                                booking=booking, 
#                                bus=bus, 
#                                board=board, 
#                                alight=alight, 
#                                seat=seat)

#     # Convert HTML to PDF
#     pdf = pdfkit.from_string(rendered, False)

#     response = make_response(pdf)
#     response.headers['Content-Type'] = 'application/pdf'
#     response.headers['Content-Disposition'] = f'attachment; filename=Ticket_{booking_id}.pdf'
    
#     return response


# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

@app.route('/download-ticket/<int:booking_id>')
@login_required
def download_ticket(booking_id):
    # A logged-in user can download only their own ticket.
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id
    ).first_or_404()

    try:
        rendered = render_template('ticket_pdf.html', booking=booking)

        # Prefer an explicit path from .env; otherwise search the system PATH.
        wkhtmltopdf_path = (
            os.environ.get('WKHTMLTOPDF_PATH')
            or shutil.which('wkhtmltopdf')
        )

        if not wkhtmltopdf_path or not os.path.isfile(wkhtmltopdf_path):
            app.logger.error(
                "wkhtmltopdf was not found. Install it or set WKHTMLTOPDF_PATH."
            )
            return (
                "PDF generation is unavailable. Install wkhtmltopdf and "
                "make sure it is available on PATH or set WKHTMLTOPDF_PATH."
            ), 503

        pdf_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        options = {
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'no-outline': None
        }

        pdf = pdfkit.from_string(
            rendered,
            False,
            configuration=pdf_config,
            options=options
        )

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=Ticket_BR_{booking_id}.pdf'
        )
        return response

    except Exception:
        app.logger.exception("Ticket PDF generation failed")
        return "Could not generate the ticket PDF. Please try again later.", 500
# ------------------------------bvibdaivbdwsvbu -----------------------------------------------
@app.route('/agency/delete-bus/<int:bus_id>', methods=['POST'])
@login_required
def delete_bus(bus_id):
    # Security check: only agencies can access this route
    if not current_user.is_agency:
        return redirect(url_for('index'))
    
    bus = Bus.query.get_or_404(bus_id)
    
    # Ensure the agency only deletes its own bus
    if bus.agency_id != current_user.agency_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('agency_dashboard'))

    try:
        # Manually delete related records to keep the database tidy
        Booking.query.filter_by(bus_id=bus_id).delete()
        Seat.query.filter_by(bus_id=bus_id).delete()
        Station.query.filter_by(bus_id=bus_id).delete()
        
        # Delete the main bus record
        db.session.delete(bus)
        db.session.commit()
        
        flash(f'Bus "{bus.name}" and all related data deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting bus: {str(e)}', 'danger')
        
    return redirect(url_for('agency_dashboard'))
# ---------------------------------------
@app.route('/agency/add-city', methods=['POST'])
@login_required
def add_city():
    if current_user.role != 'agency':
        return redirect(url_for('index'))
    
    city_name = request.form.get('city_name')
    if city_name:
        # Check if city already exists
        existing = City.query.filter_by(name=city_name).first()
        if not existing:
            new_city = City(name=city_name)
            db.session.add(new_city)
            db.session.commit()
            flash(f'City "{city_name}" added successfully!', 'success')
        else:
            flash('City already exists.', 'info')
            
    return redirect(url_for('agency_dashboard'))

@app.route('/agency/add-stop/<int:bus_id>', methods=['POST'])
@login_required
def agency_add_stop(bus_id):
    if not current_user.is_agency:
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    arrival = request.form.get('arrival')
    adjustment = float(request.form.get('adjustment') or 0.0)
    
    # Logic to get the stop order
    count = Station.query.filter_by(bus_id=bus_id).count()
    
    new_stop = Station(
        bus_id=bus_id,
        name=name,
        arrival_time=arrival,
        stop_order=count + 1,
        price_adjustment=adjustment
    )
    
    db.session.add(new_stop)
    db.session.commit()
    flash('Station added successfully!', 'success')
    return redirect(url_for('agency_dashboard'))

# ------------------------------------------

@app.route('/bus/<int:bus_id>/seats')
def seats(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    
    # Fetch all seats for this bus
    seats = Seat.query.filter_by(bus_id=bus_id).all()
    
    # Fetch all stations/stops for this bus for the dropdowns
    stations = Station.query.filter_by(bus_id=bus_id).order_by(Station.stop_order).all()
    
    return render_template('seats.html', bus=bus, seats=seats, stations=stations)


# @app.route('/calculate-dynamic-price', methods=['POST'])
# def calculate_dynamic_price():
#     data = request.get_json()
    
#     # Get station adjustments
#     b_adj = Station.query.get(data['board_id']).price_adjustment if data.get('board_id') else 0
#     a_adj = Station.query.get(data['alight_id']).price_adjustment if data.get('alight_id') else 0
    
#     # Get the specific seat's base price (this handles middle/back row pricing)
#     seat = Seat.query.get(data['seat_id'])
#     seat_base_price = seat.price if seat else 0

#     # Total = Seat Price + Boarding Adj + Alighting Adj
#     final_total = seat_base_price + b_adj + a_adj
    
#     return jsonify({
#         'success': True, 
#         'final_price': round(final_total, 2)
#     })


# @app.route('/book', methods=['POST'])
# @login_required
# def book():
#     data = request.get_json()
    
#     if not data:
#         return jsonify({'success': False, 'msg': 'No data received'})

#     bus_id = data.get('bus_id')
#     passengers = data.get('passengers')
#     board_id = data.get('board_id')  # <--- Get Boarding ID
#     alight_id = data.get('alight_id') # <--- Get Alighting ID

#     try:
#         bus = Bus.query.get(bus_id)
        
#         # Calculate Station Adjustments once for all passengers
#         b_adj = Station.query.get(board_id).price_adjustment if board_id else 0
#         a_adj = Station.query.get(alight_id).price_adjustment if alight_id else 0
#         total_station_adj = b_adj + a_adj

#         first_booking_id = None

#         for p in passengers:
#             seat_id = p.get('seat_id')
#             seat = Seat.query.get(seat_id)

#             if not seat or not seat.is_available:
#                 return jsonify({'success': False, 'msg': f'Seat {seat.seat_no if seat else "Unknown"} is already taken'})

#             # DYNAMIC CALCULATION: Seat Price + Station Adjustments
#             calculated_final_price = float(seat.price) + float(total_station_adj)

#             new_booking = Booking(
#                 user_id=current_user.id,
#                 bus_id=int(bus_id),
#                 seat_id=int(seat_id),
#                 passenger_name=str(p.get('name')),
#                 passenger_age=int(p.get('age')),
#                 passenger_gender=str(p.get('gender')),
#                 final_price=calculated_final_price # <--- This now includes everything
#             )

#             seat.is_available = False
#             db.session.add(new_booking)
#             db.session.flush() 

#             if first_booking_id is None:
#                 first_booking_id = new_booking.id

#         db.session.commit()
#         return jsonify({'success': True, 'booking_id': first_booking_id})

#     except Exception as e:
#         db.session.rollback()
#         print(f"Error: {str(e)}")
#         return jsonify({'success': False, 'msg': f"System Error: {str(e)}"})

@app.route('/calculate-dynamic-price', methods=['POST'])
def calculate_dynamic_price():
    data = request.get_json()
    
    # 1. Get station adjustments
    b_adj = Station.query.get(data['board_id']).price_adjustment if data.get('board_id') else 0
    a_adj = Station.query.get(data['alight_id']).price_adjustment if data.get('alight_id') else 0
    
    # 2. Get the specific seat's base price
    seat = Seat.query.get(data['seat_id'])
    seat_base_price = seat.price if seat else 0

    # 3. Total = Seat Price + Boarding Adj + Alighting Adj
    final_total = seat_base_price + b_adj + a_adj
    
    return jsonify({
        'success': True, 
        'final_price': round(final_total, 2) # This key MUST match JavaScript
    })

# @app.route('/book', methods=['POST'])
# @login_required
# def book():
#     data = request.get_json()
#     if not data:
#         return jsonify({'success': False, 'msg': 'No data received'})

#     bus_id = data.get('bus_id')
#     passengers = data.get('passengers')
#     board_id = data.get('board_id') 
#     alight_id = data.get('alight_id')

#     try:
#         # Calculate Station Adjustments once for the whole group
#         b_adj = Station.query.get(board_id).price_adjustment if board_id else 0
#         a_adj = Station.query.get(alight_id).price_adjustment if alight_id else 0
#         total_station_adj = b_adj + a_adj

#         first_booking_id = None

#         for p in passengers:
#             seat_id = p.get('seat_id')
#             seat = Seat.query.get(seat_id)

#             if not seat or not seat.is_available:
#                 return jsonify({'success': False, 'msg': f'Seat {seat.seat_no if seat else "Unknown"} is already taken'})

#             # DYNAMIC CALCULATION: Individual Seat Price + Station Adjustments
#             calculated_final_price = float(seat.price) + float(total_station_adj)

#             new_booking = Booking(
#                 user_id=current_user.id,
#                 bus_id=int(bus_id),
#                 seat_id=int(seat_id),
#                 passenger_name=str(p.get('name')),
#                 passenger_age=int(p.get('age')),
#                 passenger_gender=str(p.get('gender')),
#                 final_price=calculated_final_price 
#             )

#             seat.is_available = False
#             db.session.add(new_booking)
#             db.session.flush() 

#             if first_booking_id is None:
#                 first_booking_id = new_booking.id

#         db.session.commit()
#         return jsonify({'success': True, 'booking_id': first_booking_id})

#     except Exception as e:
#         db.session.rollback()
#         print(f"Error: {str(e)}")
#         return jsonify({'success': False, 'msg': f"System Error: {str(e)}"})

@app.route('/book', methods=['POST'])
@login_required
def book():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'msg': 'No data received'})

    bus_id = data.get('bus_id')
    passengers = data.get('passengers')
    board_id = data.get('board_id') 
    alight_id = data.get('alight_id')

    try:
        # Fetch station adjustments
        b_adj = Station.query.get(board_id).price_adjustment if board_id else 0
        a_adj = Station.query.get(alight_id).price_adjustment if alight_id else 0
        total_station_adj = b_adj + a_adj

        first_booking_id = None
        for p in passengers:
            seat = Seat.query.get(p.get('seat_id'))
            if not seat or not seat.is_available:
                return jsonify({'success': False, 'msg': f'Seat {seat.seat_no if seat else "Unknown"} is unavailable'})

            # Calculate final price including station adjustment
            final_calculated_price = float(seat.price) + float(total_station_adj)

            new_booking = Booking(
                user_id=current_user.id,
                bus_id=int(bus_id),
                seat_id=seat.id,
                passenger_name=p.get('name'),
                passenger_age=int(p.get('age')),
                passenger_gender=p.get('gender'),
                final_price=final_calculated_price 
            )

            seat.is_available = False
            db.session.add(new_booking)
            db.session.flush() 

            if first_booking_id is None:
                first_booking_id = new_booking.id

        db.session.commit()
        return jsonify({'success': True, 'booking_id': first_booking_id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'msg': str(e)})

# ********************************************************************************88

@app.route('/my-bookings')
@login_required
def my_bookings():
    # Fetch all bookings for the current user, newest first
    user_bookings = Booking.query.filter_by(user_id=current_user.id)\
                    .order_by(Booking.booking_date.desc()).all()
    
    return render_template('my_bookings.html', bookings=user_bookings)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
def index():
    return render_template('index.html', cities=City.query.all())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)