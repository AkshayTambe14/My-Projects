from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import text

import calendar
from datetime import datetime, date, timedelta, timezone
from functools import wraps
import smtplib
from email.message import EmailMessage
import os
import subprocess
import tempfile
import json
from vosk import Model, KaldiRecognizer
import wave
import re

from algorithms import *

#Flask, Database and Login Setup ----------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

DB_USER = 'postgres'
DB_PASS = 'about the mouse'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'postgres'

password = "urmc zfdl xsbd rnzq" 
sender = "chronocarereminders@gmail.com"

regex_pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$'

app.config['SQLALCHEMY_DATABASE_URI'] = (f'postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


#Emails -----------------------------------------------------

email_queue = Queue()

def send_email(recipient, date, pat_id):
    msg = EmailMessage()
    msg.set_content(f"This is reminder for your appointment on the date {date}, which is in the next 24 hours.")
    msg["Subject"] = "Appointment Reminder"
    msg["From"] = sender
    msg["To"] = AES_decrypt(recipient)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

    db.session.execute(text("INSERT INTO reminders (message, remind_at, patient_id) VALUES (:msg, :time, :patient_id)"), {"msg": f"This is reminder for your appointment on the date {date}, which is in the next 24 hours.", "time": date, "patient_id": pat_id})
    db.session.commit()
def enqueue_email(recipient, date, pat_id):
    print("enqueuing")
    email_queue.enqueue((recipient, date))
    process_email_queue(pat_id)
def process_email_queue(pat_id):
    while not email_queue.is_empty():
        recipient, date = email_queue.dequeue()
        send_email(recipient, date, pat_id)


#Tables/Classes ---------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date)
    phone = db.Column(db.String(100))
    salt = db.Column(db.String(64), nullable=False)

    doctor_profile = db.relationship("Doctor", uselist=False, back_populates="user")
    patient_profile = db.relationship("Patient", uselist=False, back_populates="user")
    admin_profile = db.relationship("Admin", uselist=False, back_populates="user")

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="doctor_profile")

    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=True)

    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"))
    admin = db.relationship("Admin", back_populates="doctors")

    appointments = db.relationship("Appointment", back_populates="doctor")
class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="patient_profile")

    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(50), unique=True, nullable=True)
    medical_record_number = db.Column(db.String(50), unique=True, nullable=True)

    appointments = db.relationship("Appointment", back_populates="patient")
    reminders = db.relationship("Reminder", back_populates="patient")
    conditions = db.relationship("Condition", secondary="patient_condition", back_populates="patients")
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="admin_profile")

    name = db.Column(db.String(100), nullable=False)

    doctors = db.relationship("Doctor", back_populates="admin")

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration_mins = db.Column(db.Integer, nullable=False, default=30)
    reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(50), nullable=False, default='scheduled') 
    #scheduled, completed, cancelled, noshow, requested

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')

class Reminder(db.Model):
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200), nullable=False)
    remind_at = db.Column(db.Date, nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

    patient = db.relationship("Patient", back_populates="reminders")

class Condition(db.Model):
    __tablename__ = 'conditions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    patients = db.relationship('Patient', secondary='patient_condition', back_populates='conditions')
class PatientCondition(db.Model):
    __tablename__ = 'patient_condition'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    condition_id = db.Column(db.Integer, db.ForeignKey('conditions.id'), nullable=False)
    


#Login ------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash("Access denied.", "warning")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        action = request.form.get("action")


        if action == "patient_register":
            return redirect("/patientregister")
        elif action == "doctor_register":
            return redirect("/doctorregister")
        elif action == "admin_register":
            return redirect("/adminregister")

        if not email or not password:
            flash("Email and password required", "warning")
            return redirect("/")
        
        
        user = db.session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": AES(email)}).mappings().fetchone()
        if user and verify_password(user["password_hash"], password, user["salt"]):
            user_obj = db.session.get(User, user["id"])
            login_user(user_obj)

            if user_obj.role == "doctor":
                return redirect("/doctordashboard")
            
            elif user_obj.role == "patient":
                now = datetime.now(timezone.utc)
                next_24h = now + timedelta(hours=24)

                appointments = db.session.execute(text('SELECT * FROM appointments WHERE patient_id = :patient_id'), {"patient_id": current_user.patient_profile.id}).mappings().all()  

                upcoming = []
                for appt in appointments:
                    appt_date = appt['date']
                    appt_time = appt['time']
                    appt_dt = datetime.combine(appt_date, appt_time).replace(tzinfo=timezone.utc)
                    if now <= appt_dt <= next_24h:
                        upcoming.append(appt_dt)


                if upcoming:
                    earliest = min(upcoming)
                    enqueue_email(user_obj.email, earliest.strftime("%Y-%m-%d %H:%M"), current_user.patient_profile.id)
                    
        
                return redirect("/patientdashboard")
            
            elif user_obj.role == "admin":
                return redirect("/admindashboard")
            
        flash("Invalid email or password", "warning")
        return redirect("/")
    return render_template("login.html")
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect("/")


#Registration -----------------------------------------------

@app.route("/doctorregister", methods=["GET", "POST"])
def doctor_register():
    if request.method == "POST":
        name = request.form.get("name")
        dob = request.form.get("dob")
        specialty = request.form.get("specialty")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if not(re.search(regex_pattern, password)):
            flash("Password must contain at least one number, capital letter and special character.", "warning")
            return redirect("/doctorregister")

        if password != confirmation:
            flash("Passwords do not match!", "warning")
            return redirect("/doctorregister")
        existing_user = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()
        
        if existing_user:
            flash("Email is already registered.", "warning")
            return redirect("/doctorregister")
        hashed_pw, salt = hash_password(password)
        
        try:
            db.session.execute(text("INSERT INTO users (email, password_hash, role, dob, phone, salt) VALUES (:email, :password_hash, :role, :dob, :phone, :salt)"), {"email": AES(email), "password_hash": hashed_pw, "role": "doctor", "dob": AES(dob), "phone": AES(phone), "salt": salt})
            db.session.commit()
            user_id = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()[0]
            db.session.execute(text("INSERT INTO doctors (user_id, name, specialty) VALUES (:user_id, :name, :specialty)"), {"user_id": user_id, "name": AES(name), "specialty": AES(specialty)})
            db.session.commit()
            flash("Registration Successful!", "success")
            return redirect('/')
        
        except Exception as e:
            flash(f"An error occurred", "warning")
            print(e)
            db.session.rollback()
            
    return render_template("Doctor/doc_reg.html")
@app.route("/patientregister", methods=["GET", "POST"])
def patient_register():
    if request.method == "POST":
        name = request.form.get("name")
        dob = request.form.get("dob")
        address = request.form.get("address")
        med_num = request.form.get("med_num")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        consent = request.form.get("consent")

        if consent == None:
            flash("To create an account you must consent to the terms and conditions", "warning")
            return redirect("/patientregister")

        if not(re.search(regex_pattern, password)):
            flash("Password must contain at least one number, capital letter and special character.", "warning")
            return redirect("/patientregister")
        
        if password != confirmation:
            flash("Passwords do not match.", "warning")
            return redirect("/patientregister")
        existing_user = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()
        
        if existing_user:
            flash("Email is already registered.", "warning")
            return redirect("/patientregister")
        hashed_pw, salt = hash_password(password)

        try:
            db.session.execute(text("INSERT INTO users (email, password_hash, role, dob, phone, salt) VALUES (:email, :password_hash, :role, :dob, :phone, :salt)"), {"email": AES(email), "password_hash": hashed_pw, "role": "patient", "dob": AES(dob), "phone": AES(phone), "salt": salt})
            db.session.commit()
            user_id = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()[0]
            db.session.execute(text("INSERT INTO patients (user_id, name, medical_record_number, address) VALUES (:user_id, :name, :med_num, :address)"), {"user_id": user_id, "name": AES(name), "med_num":AES(med_num), "address":AES(address)})
            db.session.commit()
            flash("Registration Successful!", "success")
            return redirect("/")
        
        except Exception as e:
            flash(f"An error occurred", "warning")
            print(e)
            db.session.rollback()

    return render_template("Patient/pat_reg.html")
@app.route("/adminregister", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        name = request.form.get("name")
        dob = request.form.get("dob")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not(re.search(regex_pattern, password)):
            flash("Password must contain at least one number, capital letter and special character.", "warning")
            return redirect("/adminregister")

        if password != confirmation:
            flash("Passwords do not match.", "warning")
            return redirect("/adminregister")
        
        existing_user = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()
        
        if existing_user:
            flash("Email is already registered.", "warning")
            return redirect("/adminregister")
        hashed_pw, salt = hash_password(password)
        
        try:
            db.session.execute(text("INSERT INTO users (email, password_hash, role, dob, phone, salt) VALUES (:email, :password_hash, :role, :dob, :phone, :salt)"), {"email": AES(email), "password_hash": hashed_pw, "role": "admin", "dob": AES(dob), "phone": AES(phone), "salt": salt})
            db.session.commit()
            user_id = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()[0]
            db.session.execute(text("INSERT INTO admins (user_id, name) VALUES (:user_id, :name)"), {"user_id": user_id, "name": AES(name)})
            db.session.commit()
            flash("Registration Successful!", "success")
            return redirect("/")
        
        except Exception as e:
            flash(f"An error occurred", "warning")
            db.session.rollback()

    return render_template("Admin/adm_reg.html")


#Calendar and Appointments ----------------------------------

def availability(db, doctor_id, appointment_date, start_time, duration):
    if isinstance(appointment_date, str):
        appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()

    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, "%H:%M").time()

    start_dt = datetime.combine(appointment_date, start_time)
    end_dt = start_dt + timedelta(minutes=duration)

    results = db.session.execute(text("SELECT 1 FROM appointments WHERE doctor_id = :doc_id AND date = :appt_date AND ((time <= :start_time AND (time + duration * interval '1 minute') > :start_time) OR (time < :end_time AND (time + duration * interval '1 minute') >= :end_time) OR (time >= :start_time AND (time + duration * interval '1 minute') <= :end_time))LIMIT 1"),{"doc_id": doctor_id,"appt_date": appointment_date,"start_time": start_time,"end_time": end_dt.time()}).fetchone()

    return results is None 
def generate_calendar_data(year, month):
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)
    today = date.today()
    
    calendar_weeks = []
    for week in weeks:
        week_days = []
        for dt in week:
            day_obj = {'day': dt.day, 'is_other_month': (dt.month != month), 'is_today': (dt == today), 'events': get_events_for_date(dt)}
            week_days.append(day_obj)
        calendar_weeks.append(week_days)

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    return {
        'month_name': calendar.month_name[month],
        'year': year,
        'month': month,
        'day_names': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'calendar_weeks': calendar_weeks,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year}
def get_events_for_date(date):

    if current_user.role == "doctor":
        rows = db.session.execute(text("SELECT a.patient_id, a.time, a.duration_mins, p.name FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.doctor_id = :doctor_id AND a.date = :date AND a.status != :cancelled"),{"doctor_id": current_user.doctor_profile.id, "date": date, "cancelled": "cancelled"}).fetchall()

    elif current_user.role == "patient":
        rows = db.session.execute(text("SELECT a.doctor_id, a.time, a.duration_mins, d.name FROM appointments a JOIN doctors d ON a.doctor_id = d.id  WHERE a.patient_id = :patient_id AND a.date = :date AND a.status != :cancelled"),{"patient_id": current_user.patient_profile.id, "date": date, "cancelled": "cancelled"}).fetchall()

    else:  
        rows = db.session.execute(text("SELECT a.patient_id, a.doctor_id, a.time, a.duration_mins, p.name as patient_name, d.name as doctor_name FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN doctors d ON a.doctor_id = d.id WHERE a.date = :date AND a.status != :cancelled"),{"date": date, "cancelled": "cancelled"}).fetchall()

    events = []
    for row in rows:
        patient_id, start_time, duration_mins, name = row

        start_dt = datetime.combine(datetime.today(), start_time)
        end_time = (start_dt + timedelta(minutes=duration_mins)).time()

        events.append({"patient_id": patient_id, "time": start_time, "duration_mins": duration_mins, "name": AES_decrypt(name), "end_time": end_time})

    return events
def add_appointment(doctor_name, patient_name, date, time, duration, reason):
    patid = db.session.execute(text("SELECT id FROM patients WHERE name = :name"), {"name": patient_name}).fetchone()
    docid = db.session.execute(text("SELECT id FROM doctors WHERE name = :name"), {"name": doctor_name}).fetchone()

    if not patid or not docid:
        flash("Invalid patient or doctor detail", "warning")


    if not availability(docid, date, time, duration):
        flash("This appointment slot is already booked.", "warning")

    db.session.execute(text("INSERT INTO appointments (patient_id, doctor_id, date, time, duration_mins, reason) VALUES (:patient_id, :doctor_id, :date, :time, :duration, :reason)"), {"patient_id": patid, "doctor_id": docid, "date": date, "time": time, "duration": duration, "reason": reason})
    db.session.commit()
    
    flash("Appointment successfully added.", "success")
def get_month_schedule(year: int, month: int):
    first_day = datetime(year, month, 1).date()
    if month == 12:
        next_month = datetime(year + 1, 1, 1).date()
    else:
        next_month = datetime(year, month + 1, 1).date()
    
    rows = db.session.execute(text("SELECT a.patient_id, a.time, a.duration_mins, a.doctor_id, a.date, p.name FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.date >= :start AND a.date < :end ORDER BY a.date, a.time"), {"start": first_day, "end": next_month}).fetchall()
    
    schedule = []
    for patient_id, start_time, duration_mins, doctor_id, appt_date, name in rows:
        start_dt = datetime.combine(appt_date, start_time)
        end_dt = start_dt + timedelta(minutes=duration_mins)
        
        schedule.append({"doctor_id": doctor_id, "patient_id": patient_id, "patient_name": AES_decrypt(name), "start": start_dt, "end": end_dt, "duration": duration_mins })
    
    return schedule

@app.route("/calendar")
@app.route("/calendar/<int:year>/<int:month>")
def doc_calendar_view(year=None, month=None):
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month
    
    if month < 1 or month > 12:
        today = date.today()
        return redirect(url_for('doc_calendar_view', year=today.year, month=today.month))
    
    calendar_data = generate_calendar_data(year, month)
    return render_template('calendar.html', **calendar_data)
@app.route("/doctorappointments/today")
def doctor_appointments_today():
    today = date.today()
    return redirect(url_for('doctor_appointments', year=today.year, month=today.month))
@app.route("/doctorappointments/navigate")
def doctor_appointments_navigate():
    year = int(request.args.get('year', date.today().year))
    month = int(request.args.get('month', date.today().month))
    direction = request.args.get('direction', 'current')
    
    if direction == 'prev':
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    elif direction == 'next':
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return redirect(url_for('doctor_appointments', year=year, month=month))
@app.route("/doctorappointments", methods=['GET', 'POST'])
@app.route("/doctorappointments/<int:year>/<int:month>", methods=['GET', 'POST'])
def doctor_appointments(year=None, month=None):
    if year is None or month is None:
        today = datetime.today()
        year = today.year
        month = today.month
    
    if month < 1 or month > 12:
        today = date.today()
        return redirect(url_for('doctor_appointments', year=today.year, month=today.month))
    
    calendar_data = generate_calendar_data(year, month)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            patient = request.form.get("patient")
            time_str = request.form.get("time")
            description = request.form.get("description")
            appdate_str = request.form.get("appdate")
            duration = int(request.form.get("duration"))

            p_id_row = db.session.execute(text("SELECT id FROM patients WHERE name = :name"), {"name": AES(patient)}).fetchone()
            if not p_id_row:
                flash("Patient not found", "warning")
                return redirect(request.url)
            p_id = p_id_row[0]

            appdate = datetime.strptime(appdate_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(time_str, "%H:%M").time()
            start_dt = datetime.combine(appdate, start_time)
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.time()

            overlap = db.session.execute(text("SELECT * FROM appointments WHERE doctor_id = :doctor_id AND date = :date AND time < :new_end AND (time + duration_mins * interval '1 minute') > :new_start LIMIT 1"), {"doctor_id": current_user.doctor_profile.id, "date": appdate, "new_start": start_time, "new_end": end_time}).fetchone()

            if overlap:
                flash("This appointment slot overlaps with an existing appointment.", "warning")
                return redirect(request.url)

            db.session.execute(text("INSERT INTO appointments (patient_id, doctor_id, date, time, duration_mins, reason, status) VALUES (:patient_id, :doctor_id, :date, :time, :duration_mins, :reason, :status)"), {"patient_id": p_id, "doctor_id": current_user.doctor_profile.id, "date": appdate, "time": start_time, "duration_mins": duration, "reason": description, "status": "scheduled"})
            db.session.commit()
            flash("Appointment successfully added.", "success")
            return redirect(url_for('doctor_appointments', year=year, month=month))
            
        elif action == "edit":
            patient = (request.form.get("patient") or "").strip()
            og_date = request.form.get("ogdate") or request.form.get("appdate")
            og_time = request.form.get("ogtime") or request.form.get("time")
            new_date = request.form.get("newdate")
            new_time = request.form.get("newtime")
            duration = request.form.get("duration")
            description = request.form.get("description") or ""

            if not patient:
                flash("Please provide the patient name to edit the appointment.", "warning")
                return redirect(request.url)

            p_row = db.session.execute(
                text("SELECT id FROM patients WHERE name = :name"), {"name": AES(patient)}).fetchone()
            if not p_row:
                flash("Patient not found.", "warning")
                return redirect(request.url)
            patient_id = p_row[0]

            appt_row = db.session.execute(text("SELECT id FROM appointments WHERE patient_id = :patient_id AND date = :ogdate AND time = :ogtime AND doctor_id = :doc_id LIMIT 1"), {"patient_id": patient_id, "ogdate": og_date, "ogtime": og_time, "doc_id": current_user.doctor_profile.id}).fetchone()

            if not appt_row:
                flash("Original appointment not found for this patient/doctor/time.", "warning")
                return redirect(request.url)
            appt_id = appt_row[0]

            try:
                db.session.execute(text("UPDATE appointments SET date = :new_date, time = :new_time, duration_mins = :duration_mins, reason = :reason, updated_at = NOW() WHERE id = :appt_id"), {"new_date": new_date, "new_time": new_time, "duration_mins": int(duration), "reason": description, "appt_id": appt_id})
                db.session.commit()
                flash("Appointment successfully edited.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error editing appointment", "warning")

            return redirect(url_for('doctor_appointments', year=year, month=month))

        elif action == "optimise":
            doctor_id = current_user.doctor_profile.id
            date = request.form.get("date")

            flash(optimise_schedule(db,doctor_id, date),"success")
            return redirect(url_for('doctor_appointments', year=year, month=month))

    patients_list = [AES_decrypt(p.name) for p in db.session.execute(text("SELECT name FROM patients")).fetchall()]
    return render_template("Doctor/doc_apmt.html", **calendar_data, patients_list=patients_list)

@app.route("/calendar")
@app.route("/calendar/<int:year>/<int:month>")
def pat_calendar_view(year=None, month=None):
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month
    
    if month < 1 or month > 12:
        today = date.today()
        return redirect(url_for('pat_calendar_view', year=today.year, month=today.month))
    
    calendar_data = generate_calendar_data(year, month)
    return render_template('calendar.html', **calendar_data)
@app.route("/patientappointments/today")
def patient_appointments_today():
    today = date.today()
    return redirect(url_for('patient_appointments', year=today.year, month=today.month))
@app.route("/patientappointments/navigate")
def patient_appointments_navigate():
    year = int(request.args.get('year', date.today().year))
    month = int(request.args.get('month', date.today().month))
    direction = request.args.get('direction', 'current')
    
    if direction == 'prev':
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    elif direction == 'next':
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return redirect(url_for('patient_appointments', year=year, month=month))
@app.route("/patientappointments", methods=['GET', 'POST'])
@app.route("/patientappointments/<int:year>/<int:month>", methods=['GET', 'POST'])
def patient_appointments(year=None, month=None):
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month
    
    if month < 1 or month > 12:
        today = date.today()
        return redirect(url_for('patient_appointments', year=today.year, month=today.month))

    calendar_data = generate_calendar_data(year, month)
    
    slots = []
    show_time_popup = False
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "get_times":
            appdate = request.form.get("date")
            doctor_name = request.form.get("doctor")
            priority = request.form.get("priority")    
        
            if not all([appdate, doctor_name, priority]):
                flash("Please fill in all fields", "warning")
                return render_template("Patient/pat_apmt.html", **calendar_data, slots=slots, show_time_popup=show_time_popup)
            
            doctor_check = db.session.execute(text("SELECT id FROM doctors WHERE name = :name"), {"name": AES(doctor_name)}).fetchone()
            
            if not doctor_check:
                flash("Doctor not found", "warning")
                return render_template("Patient/pat_apmt.html", **calendar_data, slots=slots, show_time_popup=show_time_popup)
            
            try:
                time_slots = priority_scheduling(doctor_name, appdate, priority, db)
                slots = [(start.strftime("%H:%M"), end.strftime("%H:%M")) for start, end in time_slots]
                
                if not slots:
                    flash("No available time slots for the selected date", "info")
                else:
                    show_time_popup = True
                    session['pending_appointment'] = {'doctor': doctor_name, 'date': appdate, 'priority': priority}
                    
            except Exception as e:
                flash(f"Error retrieving time slots: {str(e)}", "warning")
        
        elif action == "book_appointment":
            time_slot = request.form.get('time_slot')
            
            pending_appointment = session.get('pending_appointment')
            if not pending_appointment or not time_slot:
                flash("Invalid appointment booking request", "warning")
                return render_template("Patient/pat_apmt.html", **calendar_data, slots=slots, show_time_popup=show_time_popup)
            
            try:
                start_time_str = time_slot.split(" - ")[0]
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                
                doctor_id = db.session.execute(text("SELECT id FROM doctors WHERE name = :name"), {"name": AES(pending_appointment['doctor'])}).fetchone()[0]
                
                patient_id = current_user.patient_profile.id
                
                db.session.execute(text("INSERT INTO appointments (patient_id, doctor_id, date, time, duration_mins, priority, status) VALUES (:patient_id, :doctor_id, :date, :time, :duration_mins, :priority, :status)"), {"patient_id": patient_id, "doctor_id": doctor_id, "date": pending_appointment['date'], "time": start_time, "duration_mins": 30, "priority": pending_appointment['priority'], "status": "requested"})
                db.session.commit()
                
                session.pop('pending_appointment', None)
                
                flash("Appointment booked successfully!", "success")
                return redirect(url_for('patient_appointments', year=year, month=month))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error booking appointment: {str(e)}", "warning")

    doctor_list = [AES_decrypt(d.name) for d in db.session.execute(text("SELECT name FROM doctors")).fetchall()]
    return render_template("Patient/pat_apmt.html", **calendar_data, slots=slots, show_time_popup=show_time_popup, doctor_list=doctor_list)



#Meet -------------------------------------------------------

@app.route("/doctormeeting/<int:appointment_id>", methods=['GET', 'POST'])
@login_required
@role_required("doctor")
def doctor_meeting(appointment_id):
    appointment_row = db.session.execute(text("SELECT a.*, p.name as patient_name, p.address, p.medical_record_number, u.email, u.dob, u.phone FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN users u ON p.user_id = u.id WHERE a.id = :appointment_id"), {"appointment_id": appointment_id}).fetchone()
    appointment = {"id": appointment_row.id, "patient_id": appointment_row.patient_id, "doctor_id": appointment_row.doctor_id, "date": appointment_row.date, "time": appointment_row.time, "duration_mins": appointment_row.duration_mins, "reason": appointment_row.reason, "priority": appointment_row.priority, "status": appointment_row.status, "created_at": appointment_row.created_at, "updated_at": appointment_row.updated_at, "notes": appointment_row.notes, "patient_name": AES_decrypt(appointment_row.patient_name), "address": AES_decrypt(appointment_row.address), "medical_record_number": AES_decrypt(appointment_row.medical_record_number), "email": AES_decrypt(appointment_row.email), "dob": AES_decrypt(appointment_row.dob), "phone": AES_decrypt(appointment_row.phone)}

    previous_row = db.session.execute(text("SELECT notes, date, time FROM appointments WHERE patient_id = :patient_id AND doctor_id = :doctor_id AND id != :appointment_id AND status = 'completed' AND notes IS NOT NULL ORDER BY date DESC, time DESC LIMIT 1"),{"patient_id": appointment["patient_id"], "doctor_id": appointment["doctor_id"], "appointment_id": appointment_id}).fetchone()
    last_notes = {"notes": previous_row.notes, "date": previous_row.date, "time": previous_row.time} if previous_row else None


    if not appointment:
        flash("Appointment not found.", "warning")
        return redirect(url_for("doctor_dashboard"))
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add_note":
            new_notes = request.form.get("notes")
            db.session.execute(text("UPDATE appointments SET notes = :notes WHERE id = :appointment_id"), {"notes": new_notes, "appointment_id": appointment_id})
            db.session.commit()
            flash("Notes updated.", "success")
            return redirect(url_for("doctor_meeting", appointment_id=appointment_id))
        
        elif action == "cancel":
            db.session.execute(text("UPDATE appointments SET status = 'cancelled' WHERE id = :appointment_id"), {"appointment_id": appointment_id})
            db.session.commit()
            flash("Appointment cancelled.", "success")
            return redirect(url_for("doctor_dashboard"))
        
        elif action == "complete":
            db.session.execute(text("UPDATE appointments SET status = 'completed' WHERE id = :appointment_id"), {"appointment_id": appointment_id})
            db.session.commit()
            flash("Appointment marked as completed.", "success")
            return redirect(url_for("doctor_dashboard"))
        
        elif action == "postpone":
            new_date = request.form.get("new_date")
            new_time = request.form.get("new_time")
            db.session.execute(text("UPDATE appointments SET date = :new_date, time = :new_time WHERE id = :appointment_id"), {"new_date": new_date, "new_time": new_time, "appointment_id": appointment_id})
            db.session.commit()
            flash("Appointment postponed.", "success")
            return redirect(url_for("doctor_meeting", appointment_id=appointment_id))
        
        elif action == "add_conditions":
            patient_id = appointment["patient_id"]
            condition_names = request.form.get("conditions", "")
            condition_list = [c.strip() for c in condition_names.split(",") if c.strip()]

            try:
                for condition in condition_list:
                    encrypted_condition = AES(condition)
                    
                    existing_con = db.session.execute(text("SELECT id FROM conditions WHERE name = :name LIMIT 1"), {"name": encrypted_condition}).fetchone()

                    if existing_con:
                        condition_id = existing_con[0]
                    else:
                        db.session.execute(text("INSERT INTO conditions (name) VALUES (:name)"), {"name": encrypted_condition})
                        db.session.commit()
                        
                        condition_id = db.session.execute(text("SELECT id FROM conditions WHERE name = :name LIMIT 1"), {"name": encrypted_condition}).fetchone()[0]

                    link_exists = db.session.execute(text("SELECT 1 FROM patient_condition WHERE patient_id = :patient_id AND condition_id = :condition_id LIMIT 1"), {"patient_id": patient_id, "condition_id": condition_id}).fetchone()

                    if not link_exists:
                        db.session.execute(text("INSERT INTO patient_condition (patient_id, condition_id) VALUES (:patient_id, :condition_id)"), {"patient_id": patient_id, "condition_id": condition_id})
                        db.session.commit()

                flash("Patient conditions updated successfully.", "success")
            
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating conditions", "warning")
            
            return redirect(url_for("doctor_meeting", appointment_id=appointment_id))

        elif action == "transcribe_audio":
            audio_file = request.files.get("audio_file")
            if audio_file and audio_file.filename.lower().endswith(".wav"):
                with tempfile.TemporaryDirectory() as td:
                    path = os.path.join(td, "input.wav")
                    audio_file.save(path)

                    subprocess.run(["./ffmpeg", "-i", path, "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", os.path.join(td, "output.wav")])
                    path = os.path.join(td, "output.wav")

                    model = Model("vosk-model-small-en-us-0.15")  
                    wf = wave.open(path, "rb")

                    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                        flash("Audio file must be in the mono PCM WAV format.", "warning")
                        return redirect(url_for("doctor_meeting", appointment_id=appointment_id))
                    
                    rec = KaldiRecognizer(model, wf.getframerate())
                    transcript = ""
                    
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break

                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            transcript += result.get("text", "") + " "

                    final_result = json.loads(rec.FinalResult())
                    transcript += final_result.get("text", "")

                    old_notes = appointment["notes"] or ""
                    updated_notes = (old_notes + "\n\n[Audio Transcript]:\n" + transcript.strip()).strip()

                    db.session.execute(text("UPDATE appointments SET notes = :notes WHERE id = :appointment_id"), {"notes": updated_notes, "appointment_id": appointment_id})
                    db.session.commit()

                    flash("Audio transcribed and added to notes.", "success")
                    return redirect(url_for("doctor_meeting", appointment_id=appointment_id))
            else:
                flash("Please upload a valid .wav file.", "warning")
                return redirect(url_for("doctor_meeting", appointment_id=appointment_id))

    return render_template("Doctor/doctor_meet.html", appointment=appointment, last_notes=last_notes)


#Dashboards --------------------------------------------------

@app.route("/doctordashboard", methods=['GET','POST'])
@login_required
@role_required("doctor", "admin")
def doctor_dashboard():
    doctor = current_user.doctor_profile
    dname = AES_decrypt(doctor.name)
    appointment_rows = db.session.execute(text("SELECT a.*, p.name AS patient_name FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.doctor_id = :doctor_id AND a.date >= CURRENT_DATE AND a.status != 'completed' AND a.status != 'requested' AND a.status != 'cancelled' ORDER BY a.date ASC, a.time ASC LIMIT 5"),{"doctor_id": doctor.id}).fetchall()
    appointments = [{"id": row.id, "patient_id": row.patient_id, "doctor_id": row.doctor_id, "date": row.date, "time": row.time, "duration_mins": row.duration_mins, "reason": row.reason, "priority": row.priority, "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at, "notes": row.notes, "patient_name": AES_decrypt(row.patient_name)} for row in appointment_rows]

    next_appointment = appointments[0] if appointments else None

    return render_template("Doctor/doc_dash.html", doctor=doctor, appointments=appointments, next_appointment=next_appointment, timedelta=timedelta, datetime=datetime, dname=dname)
@app.route("/patientdashboard", methods=['GET','POST'])
@login_required
@role_required("patient")
def patient_dashboard():
    patient = current_user.patient_profile
    pname = AES_decrypt(patient.name)
    appointment_rows = db.session.execute(text("SELECT a.*, d.name AS doctor_name FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.patient_id = :patient_id AND a.date >= CURRENT_DATE AND a.status != 'completed' AND a.status != 'requested' AND a.status != 'cancelled' ORDER BY a.date ASC, a.time ASC LIMIT 5"), {"patient_id": patient.id}).fetchall()
    appointments = [{"id": row.id, "patient_id": row.patient_id, "doctor_id": row.doctor_id, "date": row.date, "time": row.time, "duration_mins": row.duration_mins, "reason": row.reason, "priority": row.priority, "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at, "notes": row.notes, "doctor_name": AES_decrypt(row.doctor_name)} for row in appointment_rows]
    
    return render_template("Patient/pat_dash.html", pname=pname, patient=patient, appointments=appointments, timedelta=timedelta, datetime=datetime)
@app.route("/admindashboard", methods=['GET','POST'])
@login_required
@role_required("admin")
def admin_dashboard():
    if request.method == 'POST':
        patient_name = request.form.get('patient')
        date = request.form.get('date')
        time = request.form.get('time')
        reason = request.form.get('reason')
        duration = request.form.get('duration')
        priority = request.form.get('priority')
        doctor_id = request.form.get('doctor_id')

        if doctor_id is None or doctor_id.strip() == "":
            flash("Please select a doctor.", "warning")
            return redirect(url_for('admin_dashboard'))

        doctor_id = int(doctor_id)  


        if not all([patient_name, doctor_id, date, time, reason, duration, priority]):
            flash("Please fill in all required fields.", "warning")
        else:
            patient_row = db.session.execute(text("SELECT id FROM patients WHERE name = :name"), {"name": AES(patient_name)}).fetchone()

            if not patient_row:
                flash("Patient not found.", "error")
            else:
                patient_id = patient_row.id
                try:
                    db.session.execute(text("INSERT INTO appointments (patient_id, doctor_id, date, time, reason, duration_mins, priority, status) VALUES (:patient_id, :doctor_id, :date, :time, :reason, :duration, :priority, 'requested')"), {"patient_id": patient_id, "doctor_id": doctor_id, "date": date, "time": time, "reason": reason, "duration": duration, "priority": priority})
                    db.session.commit()
                    flash("Appointment booked successfully!", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error booking appointment", "error")

    doctor_rows = db.session.execute(text("SELECT d.id, d.user_id, d.name, d.specialty, d.admin_id, u.email, u.phone FROM doctors d JOIN users u ON d.user_id = u.id WHERE d.admin_id = :admin_id"), {"admin_id": current_user.admin_profile.id}).fetchall()
    doctors = [{"id": row.id, "user_id": row.user_id, "name": AES_decrypt(row.name), "specialty": AES_decrypt(row.specialty), "admin_id": row.admin_id, "email": AES_decrypt(row.email), "phone": AES_decrypt(row.phone)} for row in doctor_rows]

    patient_rows = db.session.execute(text("SELECT p.id, p.user_id, p.name, p.address, p.medical_record_number, u.email FROM patients p JOIN users u ON p.user_id = u.id")).fetchall()
    patients = [{"id": row.id, "user_id": row.user_id, "name": AES_decrypt(row.name), "address": AES_decrypt(row.address), "medical_record_number": AES_decrypt(row.medical_record_number), "email": AES_decrypt(row.email)} for row in patient_rows]

    if not doctors:
        flash("No linked doctors, please link doctors to book appointments", "warning")

    return render_template("Admin/adm_dash.html", doctors=doctors, patients=patients)


#Profile/Settings --------------------------------------------

@app.route("/doctorprofile", methods=['GET','POST'])
@login_required
@role_required("doctor", "admin")
def doctor_profile():
    d_id = current_user.doctor_profile.id
    doctor_info_row = db.session.execute(text("SELECT d.*, u.email, u.phone, u.dob FROM doctors d JOIN users u ON d.user_id = u.id WHERE d.id = :doc_id"), {"doc_id": d_id}).fetchone()
    doctor_info = {"id": doctor_info_row.id, "user_id": doctor_info_row.user_id, "name": AES_decrypt(doctor_info_row.name), "specialty": AES_decrypt(doctor_info_row.specialty), "admin_id": doctor_info_row.admin_id, "email": AES_decrypt(doctor_info_row.email), "phone": AES_decrypt(doctor_info_row.phone), "dob": AES_decrypt(doctor_info_row.dob)}

    return render_template("Doctor/doc_profile.html", doctor=doctor_info)
@app.route("/patientprofile", methods=['GET','POST'])
@login_required
@role_required("patient", "admin", "doctor")
def patient_profile():
    p_id = current_user.patient_profile.id if current_user.role == "patient" else request.args.get("id")
    patient_info = db.session.execute(text("SELECT p.*, u.email, u.phone, u.dob FROM patients p JOIN users u ON p.user_id = u.id WHERE p.id = :pat_id"), {"pat_id": p_id}).fetchone()
    patient_info = {"id": patient_info.id, "user_id": patient_info.user_id, "name": AES_decrypt(patient_info.name), "address": AES_decrypt(patient_info.address), "medical_record_number": AES_decrypt(patient_info.medical_record_number), "email": AES_decrypt(patient_info.email), "phone": AES_decrypt(patient_info.phone), "dob": AES_decrypt(patient_info.dob)}
    
    return render_template("Patient/pat_profile.html", patient=patient_info)
@app.route("/adminprofile", methods=['GET','POST'])
@login_required
@role_required("admin", "doctor")
def admin_profile():
    a_id = current_user.admin_profile.id if current_user.role == "admin" else request.args.get("id")
    admin_info = db.session.execute(text("SELECT a.*, u.email, u.phone, u.dob FROM admins a JOIN users u ON a.user_id = u.id WHERE a.id = :admin_id"), {"admin_id": a_id}).fetchone()
    admin_info = {"id": admin_info.id, "user_id": admin_info.user_id, "name": AES_decrypt(admin_info.name), "email": AES_decrypt(admin_info.email), "phone": AES_decrypt(admin_info.phone), "dob": AES_decrypt(admin_info.dob)}
    
    doctor_rows = db.session.execute(text("SELECT d.*, u.* FROM doctors AS d JOIN users AS u ON d.user_id = u.id")).fetchall()    
    doctors = [{"id": row.id, "user_id": row.user_id, "name": AES_decrypt(row.name), "specialty": AES_decrypt(row.specialty), "admin_id": row.admin_id, "email": AES_decrypt(row.email), "phone": AES_decrypt(row.phone), "dob": AES_decrypt(row.dob)} for row in doctor_rows]
    
    if request.method == "POST":
        docs_raw = request.form.getlist("doctors")
        docs = json.loads(docs_raw[0])
        for doctor in docs:
            doc_id_row = db.session.execute(text("SELECT id FROM doctors WHERE name = :name"),{"name": AES(doctor)}).fetchone()
            if doc_id_row:
                db.session.execute(text("UPDATE doctors SET admin_id = :admin_id WHERE id = :doc_id"), {"admin_id": a_id, "doc_id": doc_id_row.id})
        
        db.session.commit()

    return render_template("Admin/adm_profile.html", admin=admin_info, doctors=doctors)


#Records -----------------------------------------------------

@app.route("/records", methods=['GET', 'POST'])
@login_required
@role_required("doctor", "admin")
def records():
    conditions_rows = db.session.execute(text("SELECT * FROM conditions")).fetchall()
    conditions = [AES_decrypt(row.name) for row in conditions_rows]

    patients_rows = db.session.execute(text("SELECT p.id as pid, p.user_id, p.name as pname, p.address, p.medical_record_number, u.email as uemail, u.phone as uphone, u.dob as udob FROM patients AS p JOIN users AS u ON p.user_id = u.id")).mappings().fetchall()
    patients = [{"id": row["pid"], "user_id": row["user_id"], "name": AES_decrypt(row["pname"]), "address": AES_decrypt(row["address"]), "medical_record_number": AES_decrypt(row["medical_record_number"]), "email": AES_decrypt(row["uemail"]), "phone": AES_decrypt(row["uphone"]), "dob": AES_decrypt(row["udob"])} for row in patients_rows]


    patient_conditions = {}
    for p in patients:
        cond_rows = db.session.execute(text("SELECT c.name FROM patient_condition pc JOIN conditions c ON pc.condition_id = c.id WHERE pc.patient_id = :pid"), {"pid": p["id"]}).fetchall()
        cond_list = [AES_decrypt(r[0]) for r in cond_rows] if cond_rows else []
        patient_conditions[p["id"]] = cond_list
        p["conditions"] = cond_list

    sort = request.form.get('action') == "sort" if request.method == "POST" else False

    if sort:
        names = [patient['name'] for patient in patients]
        sorted_list = merge_sort(names)
        sorted_patients = [next(p for p in patients if p['name'] == name) for name in sorted_list]
        patients = sorted_patients

    if request.method == "POST":
        if request.form.get("action") == "add":
            name = request.form.get("name")
            dob = request.form.get("dob")
            phone = request.form.get("phone")
            email = request.form.get("email")
            address = request.form.get("address")
            med_num = request.form.get("med_num")

            db.session.execute(text("INSERT INTO users (email, password_hash, role, dob, phone, salt) VALUES (:email, NULL, :role, :dob, :phone, NULL)"), {"email": AES(email), "role": "patient", "dob": AES(dob), "phone": AES(phone)})
            db.session.commit()

            user_id = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()[0]

            db.session.execute(text("INSERT INTO patients (user_id, name, medical_record_number, address) VALUES (:user_id, :name, :medical_record_number, :address)"), {"user_id": user_id, "name": AES(name), "medical_record_number": AES(med_num), "address": AES(address)})
            db.session.commit()
            return redirect("/records")
        
        elif request.form.get("action") == "delete_condition":
            patient_id = request.form.get("patient_id")
            condition_name = request.form.get("condition_name")
            
            try:
                condition_row = db.session.execute(text("SELECT id FROM conditions WHERE name = :name"), {"name": AES(condition_name)}).fetchone()
                
                if condition_row:
                    condition_id = condition_row[0]
                    
                    db.session.execute(
                        text("DELETE FROM patient_condition WHERE patient_id = :patient_id AND condition_id = :condition_id"),
                        {"patient_id": patient_id, "condition_id": condition_id}
                    )
                    db.session.commit()
                    flash("Condition removed successfully.", "success")
                else:
                    flash("Condition not found.", "warning")
                    
            except Exception as e:
                db.session.rollback()
                flash("Error removing condition.", "warning")
                print(e)
            
            return redirect("/records")

    return render_template("Doctor/records.html", patients=patients, conditions=conditions, patient_conditions=patient_conditions)

#History ------------------------------------------------------

@app.route("/history", methods=['GET', 'POST'])
@login_required
@role_required("doctor", "admin", "patient")
def history():
    patient_id = current_user.patient_profile.id
    
    done_rows = db.session.execute(text("SELECT a.*, d.name FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.status = 'completed' AND a.patient_id = :patient_id"), {"patient_id": patient_id}).fetchall()
    sched_rows = db.session.execute(text("SELECT a.*, d.name FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.status = 'scheduled' AND a.patient_id = :patient_id"), {"patient_id": patient_id}).fetchall()
    

    done_apps = LinkedList()
    for row in done_rows:
        row_dict = {
            'id': row[0],
            'patient_id': row[1],
            'doctor_id': row[2],
            'date': row[3],
            'time': row[4],
            'duration_mins': row[5],
            'reason': row[6],
            'notes': row[7],
            'priority': row[8],
            'status': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'name': AES_decrypt(row[12])}
        done_apps.append(row_dict)

    sched_apps = LinkedList()
    for row in sched_rows:
        row_dict = {
            'id': row[0],
            'patient_id': row[1],
            'doctor_id': row[2],
            'date': row[3],
            'time': row[4],
            'duration_mins': row[5],
            'reason': row[6],
            'notes': row[7],
            'priority': row[8],
            'status': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'name': AES_decrypt(row[12])}
        sched_apps.append(row_dict)

    return render_template("Patient/history.html", done_apps=done_apps, sched_apps=sched_apps)


#Patients ------------------------------------------------------

@app.route("/patients", methods=['GET','POST'])
@login_required
@role_required("admin")
def patients():
    conditions_rows = db.session.execute(text("SELECT * FROM conditions")).fetchall()
    conditions = [{"id": row.id, "name": AES_decrypt(row.name)} for row in conditions_rows]

    patients_rows = db.session.execute(text("SELECT p.*, u.* FROM patients AS p JOIN users AS u ON p.user_id = u.id")).fetchall()
    patients = [{"id": row.id, "user_id": row.user_id, "name": AES_decrypt(row.name), "address": AES_decrypt(row.address), "medical_record_number": AES_decrypt(row.medical_record_number), "email": AES_decrypt(row.email), "phone": AES_decrypt(row.phone), "dob": AES_decrypt(row.dob)} for row in patients_rows]

    patient_conditions = {}
    for p in patients:
        cond_rows = db.session.execute(text("SELECT c.name FROM patient_condition pc JOIN conditions c ON pc.condition_id = c.id WHERE pc.patient_id = :pid"), {"pid": p["id"]}).fetchall()
        cond_list = [AES_decrypt(r[0]) for r in cond_rows] if cond_rows else []
        patient_conditions[p["id"]] = cond_list
        p["conditions"] = cond_list

    sort = request.form.get('action') == "sort" if request.method == "POST" else False

    if sort:
        names = [patient['name'] for patient in patients]
        sorted_list = merge_sort(names)
        sorted_patients = [next(p for p in patients if p['name'] == name) for name in sorted_list]
        patients = sorted_patients

    if request.method == "POST":
        if request.form.get("action") == "add":
            name = request.form.get("name")
            dob = request.form.get("dob")
            phone = request.form.get("phone")
            email = request.form.get("email")
            address = request.form.get("address")
            med_num = request.form.get("med_num")

            db.session.execute(text("INSERT INTO users (email, password_hash, role, dob, phone) VALUES (:email, NULL, :role, :dob, :phone)"), {"email": AES(email), "role": "patient", "dob": AES(dob), "phone": AES(phone)})
            db.session.commit()

            user_id = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()[0]

            db.session.execute(text("INSERT INTO patients (user_id, name, medical_record_number, address) VALUES (:user_id, :name, :medical_record_number, :address)"), {"user_id": user_id, "name": AES(name), "medical_record_number": AES(med_num), "address": AES(address)})
            db.session.commit()
            return redirect("/patients")

    return render_template("Admin/patients.html", patients=patients, conditions=conditions, patient_conditions=patient_conditions)
    


#Doctors -------------------------------------------------------

@app.route("/doctors", methods=['GET','POST'])
@login_required
@role_required("admin")
def doctors():
    doctor_rows = db.session.execute(text("SELECT d.*, u.* FROM doctors AS d JOIN users AS u ON d.user_id = u.id")).mappings().fetchall()
    doctors = [{"id": row.id, "user_id": row.user_id, "name": AES_decrypt(row.name), "specialty": AES_decrypt(row.specialty), "admin_id": row.admin_id, "email": AES_decrypt(row.email), "phone": AES_decrypt(row.phone), "dob": AES_decrypt(row.dob)} for row in doctor_rows]

    sort = request.form.get('action') == "sort" if request.method == "POST" else False

    if sort:
        names = [doctor['name'] for doctor in doctors]
        sorted_list = merge_sort(names)
        sorted_doctors = [next(d for d in doctors if d['name'] == name) for name in sorted_list]
        doctors = sorted_doctors

    if request.method == "POST":
        if request.form.get("action") == "add":
            name = request.form.get("name")
            dob = request.form.get("dob")
            phone = request.form.get("phone")
            email = request.form.get("email")
            specialty = request.form.get("specialty")

            db.session.execute(text("INSERT INTO users (email, password_hash, role, dob, phone) VALUES (:email, NULL, :role, :dob, :phone)"), {"email": AES(email), "role": "patient", "dob": AES(dob), "phone": AES(phone)})
            db.session.commit()

            user_id = db.session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": AES(email)}).fetchone()[0]

            db.session.execute(text("INSERT INTO doctors (user_id, name, specialty) VALUES (:user_id, :name, :specialty)"), {"user_id": user_id, "name": AES(name), "specialty": AES(specialty)})
            db.session.commit()
            print("Doctor added successfully.")
            return redirect("/doctors")

    return render_template("Admin/doctors.html", doctors=doctors)


#Requests -------------------------------------------------------

@app.route("/doctorrequests", methods=["GET"])
@login_required
@role_required("doctor")
def doctor_requests():
    doctor_id = current_user.doctor_profile.id
    request_rows = db.session.execute(text("SELECT a.*, p.name as patient_name FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.doctor_id = :doctor_id AND a.status = 'requested' ORDER BY a.date, a.time"), {"doctor_id": doctor_id}).fetchall()
    requests = [{"id": row.id, "patient_id": row.patient_id, "doctor_id": row.doctor_id, "date": row.date, "time": row.time, "duration_mins": row.duration_mins, "reason": row.reason, "priority": row.priority, "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at, "notes": row.notes, "patient_name": AES_decrypt(row.patient_name)} for row in request_rows]

    return render_template("Doctor/doc_req.html", requests=requests)  

@app.route("/doctorrequests/<int:request_id>", methods=["POST"])
@login_required
@role_required("doctor")
def review_request(request_id):
    action = request.form.get("action")
    appt = db.session.execute(text("SELECT * FROM appointments WHERE id = :id"), {"id": request_id}).fetchone()
    
    if not appt:
        flash("Request not found.", "warning")
        return redirect(url_for("doctor_requests"))

    if action == "approve":
        db.session.execute(text("UPDATE appointments SET status = 'scheduled' WHERE id = :id"), {"id": request_id})
        db.session.commit()
        flash("Appointment approved and scheduled.", "success")

    elif action == "reject":
        db.session.execute(text("UPDATE appointments SET status = 'cancelled' WHERE id = :id"), {"id": request_id})
        db.session.commit()
        flash("Appointment request rejected.", "info")
    return redirect(url_for("doctor_requests"))


#Running the Flask App -------------------------------------------

if __name__ == '__main__':
    #Creates all the tables in PostgreSQL
    with app.app_context():
        db.create_all()
    app.run(debug=True)
