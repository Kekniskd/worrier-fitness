from flask_login import UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(10), unique=True, nullable=True)  # For attendance marking
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    join_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    trainer = db.relationship('Staff', backref=db.backref('trainees', lazy=True))
    attendances = db.relationship('Attendance', backref='user', lazy=True)
    membership = db.relationship('Membership', backref='user', lazy=True)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in months
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    memberships = db.relationship('Membership', backref='plan', lazy=True)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    position = db.Column(db.String(50), nullable=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    salary = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    attendance = db.relationship('StaffAttendance', backref='staff', lazy=True)
    payments = db.relationship('StaffPayment', backref='staff', lazy=True)

class StaffAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')  # present, absent, late, half-day

class StaffPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_for_month = db.Column(db.Date, nullable=False)  # Month for which payment is made
    status = db.Column(db.String(20), default='pending')  # pending, paid, delayed
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text) 