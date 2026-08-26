# Vehicle Breakdown Management System

A web app where customers can report vehicle breakdowns and request roadside
assistance, and admins/mechanics can track and resolve those requests.

**Tech stack:** Python (Flask), MySQL/SQLite (SQLAlchemy ORM), HTML, CSS

## Features
- Customer registration & login (passwords hashed with Werkzeug)
- Submit a breakdown request: vehicle number, type, issue, location, contact
- Track request status: Pending → In Progress → Resolved
- Admin dashboard: view all requests, filter by status, update status & add
  mechanic notes, see live stats (total/pending/in-progress/resolved)

## Project Structure
```
vehicle_breakdown_system/
├── app.py                  # Flask app: routes, models, auth
├── database.sql            # MySQL schema (if you want raw MySQL instead of SQLite)
├── requirements.txt
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── request_form.html
│   ├── request_detail.html
│   └── admin_dashboard.html
└── static/css/style.css
```

## Setup & Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the app (creates the SQLite DB and a default admin account automatically):
   ```
   python app.py
   ```

3. Open **http://localhost:5000** in your browser.

4. Log in as admin to manage requests:
   - Email: `admin@breakdown.com`
   - Password: `admin123`

   Or register as a new customer to submit a breakdown request.

## Switching to MySQL

By default this runs on SQLite so it works with zero setup. To use MySQL
(as listed on the resume):

1. `pip install pymysql`
2. Create the database: `CREATE DATABASE vehicle_breakdown_db;`
3. In `app.py`, replace the `SQLALCHEMY_DATABASE_URI` line with:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://<user>:<password>@localhost/vehicle_breakdown_db'
   ```
4. Run `python app.py` again — tables are created automatically.

(`database.sql` is also included if you'd rather create the tables manually.)

## How to talk about this in an interview
- **Architecture**: Flask (MVC-ish: models in `app.py`, views as Jinja2
  templates, routes as controllers), server-rendered HTML (no separate
  frontend framework), session-based authentication.
- **Auth**: passwords are never stored in plain text — hashed with
  Werkzeug's `generate_password_hash`/`check_password_hash`.
- **Access control**: `@login_required` and `@admin_required` decorators
  guard routes; customers can only view their own requests.
- **Data model**: one-to-many between `User` and `BreakdownRequest`.
- **Possible extensions**: email/SMS notifications on status change,
  mechanic assignment (separate mechanic role), live map with geolocation,
  REST API + JS frontend instead of server-rendered templates.
