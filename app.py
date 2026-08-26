"""
Vehicle Breakdown Management System
------------------------------------
A Flask web application that lets customers report vehicle breakdowns
and request roadside assistance, while admins/mechanics manage and
resolve those requests.

Tech stack: Python (Flask), MySQL (via SQLAlchemy - SQLite used by
default for easy local demo, see DATABASE CONFIG below to switch to
MySQL), HTML, CSS.
"""

import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'

# ------------------------------------------------------------------
# DATABASE CONFIG
# ------------------------------------------------------------------
# Default: SQLite (works instantly, no server needed - good for demo
# and for running this project locally / showing in an interview).
#
# To use MySQL instead (as listed on your resume), install PyMySQL
# (`pip install pymysql`) and replace the line below with:
#
#   app.config['SQLALCHEMY_DATABASE_URI'] = (
#       'mysql+pymysql://<username>:<password>@localhost/vehicle_breakdown_db'
#   )
#
# Then create the database first: `CREATE DATABASE vehicle_breakdown_db;`
# The database.sql file included in this project has the equivalent
# raw MySQL schema if you want to create tables manually instead of
# letting SQLAlchemy generate them.
# ------------------------------------------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'breakdown_system.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ------------------------------------------------------------------
# MODELS
# ------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'customer' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('BreakdownRequest', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BreakdownRequest(db.Model):
    __tablename__ = 'breakdown_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending / In Progress / Resolved
    mechanic_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ------------------------------------------------------------------
# AUTH HELPERS
# ------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------
# ROUTES - PUBLIC
# ------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('register'))

        user = User(name=name, email=email, phone=phone, role='customer')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# ------------------------------------------------------------------
# ROUTES - CUSTOMER
# ------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    my_requests = BreakdownRequest.query.filter_by(
        user_id=session['user_id']
    ).order_by(BreakdownRequest.created_at.desc()).all()

    return render_template('dashboard.html', requests=my_requests)


@app.route('/request/new', methods=['GET', 'POST'])
@login_required
def new_request():
    if request.method == 'POST':
        req = BreakdownRequest(
            user_id=session['user_id'],
            vehicle_number=request.form['vehicle_number'].strip().upper(),
            vehicle_type=request.form['vehicle_type'],
            issue_description=request.form['issue_description'].strip(),
            location=request.form['location'].strip(),
            contact_number=request.form['contact_number'].strip(),
        )
        db.session.add(req)
        db.session.commit()
        flash('Breakdown request submitted! Help is on the way.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('request_form.html')


@app.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    req = BreakdownRequest.query.get_or_404(request_id)
    if req.user_id != session['user_id'] and session.get('role') != 'admin':
        flash('You do not have access to that request.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('request_detail.html', req=req)


# ------------------------------------------------------------------
# ROUTES - ADMIN
# ------------------------------------------------------------------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    status_filter = request.args.get('status', 'All')
    query = BreakdownRequest.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)
    all_requests = query.order_by(BreakdownRequest.created_at.desc()).all()

    stats = {
        'total': BreakdownRequest.query.count(),
        'pending': BreakdownRequest.query.filter_by(status='Pending').count(),
        'in_progress': BreakdownRequest.query.filter_by(status='In Progress').count(),
        'resolved': BreakdownRequest.query.filter_by(status='Resolved').count(),
    }

    return render_template('admin_dashboard.html', requests=all_requests, stats=stats, status_filter=status_filter)


@app.route('/admin/request/<int:request_id>/update', methods=['POST'])
@login_required
@admin_required
def update_request(request_id):
    req = BreakdownRequest.query.get_or_404(request_id)
    req.status = request.form['status']
    req.mechanic_notes = request.form.get('mechanic_notes', '').strip()
    db.session.commit()
    flash(f'Request #{req.id} updated to "{req.status}".', 'success')
    return redirect(url_for('admin_dashboard'))


# ------------------------------------------------------------------
# CLI / STARTUP - create tables and a default admin account
# ------------------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@breakdown.com').first():
            admin = User(
                name='Admin',
                email='admin@breakdown.com',
                phone='9999999999',
                role='admin',
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created -> email: admin@breakdown.com | password: admin123")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
