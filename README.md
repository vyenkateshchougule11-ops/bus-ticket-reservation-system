# Bus Ticket Reservation System

A web-based Bus Ticket Reservation System built using **Python, Flask, SQLAlchemy, SQLite, HTML, CSS, JavaScript and Bootstrap**. The application provides a platform for users to search buses, select seats, calculate ticket prices and manage their bookings. It also supports agency registration and bus management.

The project uses SQLite as its default database, making local setup simple without requiring a separate database server.

## Features

### User Functionality
- User registration and login.
- Search buses by source and destination.
- View available buses and their details.
- View bus seat layouts.
- Select seats and calculate ticket prices.
- Dynamic seat pricing based on seat selection.
- Passenger information and booking management.
- View booking history.
- Download booking tickets in PDF format.

### Bus Agency Functionality
- Agency registration and login.
- Agency dashboard.
- Add and manage buses.
- Configure bus details, routes and schedules.
- Add cities and intermediate stops.
- Configure bus amenities.
- Automatic seat generation based on bus type.
- Manage agency-owned buses.

### Additional Features
- Role-based user functionality.
- Password hashing.
- SQLAlchemy ORM for database operations.
- SQLite database integration.
- PDF ticket generation using PDFKit and wkhtmltopdf.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Template Engine | Jinja2 |
| Authentication | Flask-Login |
| Password Security | Werkzeug |
| PDF Generation | PDFKit, wkhtmltopdf |
| Environment Configuration | python-dotenv |

## Project Structure

```text
Bus-Ticket-Reservation/
│
├── app.py
├── init_db.py
├── seed_all.py
├── import_buses_csv.py
├── buses.csv
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── migrations/
│
├── static/
│   └── bus_images/
│
└── templates/
    ├── admin.html
    ├── agency_dashboard.html
    ├── base.html
    ├── booking_success.html
    ├── index.html
    ├── login.html
    ├── my_bookings.html
    ├── register.html
    ├── register_agency.html
    ├── search.html
    ├── seats.html
    └── ticket_pdf.html
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vyenkateshchougule11-ops/bus-ticket-reservation-system.git

cd bus-ticket-reservation-system
```

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv

.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file by copying `.env.example`.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

Update the `.env` file:

```env
SECRET_KEY=your-own-secure-secret-key

DB_URL=sqlite:///redbus.db

WKHTMLTOPDF_PATH=
```

- `SECRET_KEY`: Use a randomly generated secret key.
- `DB_URL`: SQLite database configuration.
- `WKHTMLTOPDF_PATH`: Optional path to the wkhtmltopdf executable.

Keep `.env` private and never commit it to GitHub.

### 5. Initialize and Run the Application

Run:

```bash
python app.py
```

The application creates the database tables using SQLAlchemy when the application starts.

### 6. Open the Application

Visit:

```text
http://127.0.0.1:5000
```

## Database

The application uses **SQLite with Flask-SQLAlchemy**.

The database stores application information such as:

- Users
- Agencies
- Cities
- Buses
- Seats
- Stations
- Bookings

The SQLite database is generated locally when the application is initialized.

## PDF Ticket Generation

The application uses PDFKit to generate downloadable booking tickets.

PDF generation requires the external **wkhtmltopdf** executable in addition to the Python `pdfkit` package.

Install wkhtmltopdf separately and either:

- Add its executable to your system PATH, or
- Configure its location using `WKHTMLTOPDF_PATH` in `.env`.

PDF generation will not work until this external dependency is configured.

## Security Considerations

- Passwords are stored using password hashing.
- Secret keys and environment-specific configuration are kept outside the public repository.
- The `.env` file and local database files are excluded using `.gitignore`.
- Production deployment should include CSRF protection, stronger input validation, secure session configuration and appropriate authorization checks.

## Future Improvements

- Online payment gateway integration.
- Email and SMS booking notifications.
- Improved responsive user interface.
- Enhanced administrative dashboard.
- Production deployment and hosting.
- Automated testing and improved application security.

## Author

**Vyenkatesh Chougule**

- GitHub: [@vyenkateshchougule11-ops](https://github.com/vyenkateshchougule11-ops)
- LinkedIn: [Connect with me](https://www.linkedin.com/in/vyenkatesh-chougule-a46799390/)

---

*This project was developed as a practical full-stack web application to demonstrate Python backend development, database integration, authentication and reservation management.*