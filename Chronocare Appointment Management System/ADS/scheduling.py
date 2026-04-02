from sqlalchemy import text
from datetime import datetime, time, timedelta
from algorithms import *

def priority_scheduling(doctor_name, appointment_date, priority, db, start_hour=9, end_hour=17, duration=60, step_minutes=None):
    appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    start = time(start_hour, 0)
    end = time(end_hour, 0)

    doctor_row = db.session.execute(text("SELECT id FROM doctors WHERE name = :name"),{"name": AES(doctor_name)}).fetchone()
    
    if not doctor_row:
        return []

    doctor_id = doctor_row[0]

    existing_apps = db.session.execute(text("SELECT * FROM appointments WHERE doctor_id = :doctor_id AND time >= :start AND time < :end AND date = :appointment_date ORDER BY time"),{"doctor_id": doctor_id, "start": start, "end": end, "appointment_date": appointment_date}).fetchall()

    free_slots = []
    current_time = datetime.combine(appointment_date, start)
    slot_step = timedelta(minutes=duration if step_minutes is None else step_minutes)

    for app in existing_apps:
        app_start = datetime.combine(appointment_date, app.time)
        app_end = app_start + timedelta(minutes=app.duration_mins)

        if app_start > current_time:
            gap_start = current_time
            while (gap_start + timedelta(minutes=duration)) <= app_start:
                free_slots.append((gap_start, gap_start + timedelta(minutes=duration)))
                gap_start += slot_step

        current_time = max(current_time, app_end)

    # Final slot after last appointment
    work_end_dt = datetime.combine(appointment_date, end)
    gap_start = current_time
    while (gap_start + timedelta(minutes=duration)) <= work_end_dt:
        free_slots.append((gap_start, gap_start + timedelta(minutes=duration)))
        gap_start += slot_step

    priority = priority.lower()
    if priority == "urgent":
        return free_slots[:1]
    elif priority == "high":
        return free_slots[:3]
    elif priority in ("low", "neutral"):
        return free_slots

    # If priority is not valid, return all slots
    return free_slots
