# RedBus Clone (Flask) - Local DB (SQLite) + Optional MySQL

This is a complete minimal RedBus-like application using Flask, SQLAlchemy and simple Jinja2 templates.
By default it uses SQLite for local development. You can optionally configure a local MySQL server via `DB_URL` in `.env`.

## What's included
- app.py : Flask app + routes + models
- templates/ : Jinja2 templates for index, login, register, search, seats, admin
- static/ : simple CSS
- init_db.py : Creates tables and seeds admin + cities (works for SQLite & MySQL)
- import_buses_csv.py : Imports buses.csv (example provided)
- buses.csv : 5 sample buses
- seed_all.py : Seeds users, cities, buses, seats and bookings
- requirements.txt, .env.example

## Quick start (SQLite - easiest)

1. Create and activate virtualenv:
   ```bash
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # Linux / macOS
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` (optional):
   ```bash
   copy .env.example .env   # Windows (cmd) or use your editor
   cp .env.example .env    # Linux/macOS
   ```
   Leave `DB_URL` blank to use SQLite `redbus.db` in project folder.

4. Initialize DB and seed minimal data:
   ```bash
   python init_db.py
   ```

5. (Optional) Import sample buses:
   ```bash
   python import_buses_csv.py
   ```

6. Run the app:
   ```bash
   flask run
   ```
   or
   ```bash
   python app.py
   ```
   Open http://127.0.0.1:5000

Default admin: admin@example.com / adminpass

## Use MySQL instead of SQLite
1. Create MySQL database and user (example):
   ```sql
   CREATE DATABASE redbus_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'rbuser'@'localhost' IDENTIFIED WITH mysql_native_password BY 'rbpass';
   GRANT ALL PRIVILEGES ON redbus_db.* TO 'rbuser'@'localhost';
   FLUSH PRIVILEGES;
   ```
2. In `.env`, set `DB_URL`:
   ```env
   DB_URL=mysql+pymysql://rbuser:rbpass@127.0.0.1:3306/redbus_db?charset=utf8mb4
   ```
3. Install dependencies and run `python init_db.py` as above.

## Notes & Security
- `.env` contains secrets; don't commit it to git. Add `.env` to `.gitignore`.
- Passwords in sample data are hashed.
- For production use, add CSRF protection, input validation, and a real payment integration.
