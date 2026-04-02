from sqlalchemy import text
from datetime import datetime, timedelta, time
import random as rand
import numpy as np

work_start = time(8, 0)
work_end = time(19, 0)

def optimise_schedule(db, doctor_id, appointment_date, initial_temp=100, min_temp=1, iterations=200, cool_rate=0.95):
    #Optimises schedule for doctor on specific date

    schedule = get_schedule_from_db(db, doctor_id, appointment_date)
    if not schedule:
        return "No appointments found for this doctor/date"

    optimised = simulated_annealing(schedule, initial_temp, min_temp, iterations, cool_rate)
    save_schedule_to_db(db, optimised)
    return "Schedule optimised successfully"

def get_schedule_from_db(db, doctor_id, appointment_date):
    #Gets all appointments for a doctor on specific date.
    #Returns a list of tuples
    
    if isinstance(appointment_date, str):
        appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    else:
        appointment_date_obj = appointment_date

    results = db.session.execute(text("SELECT id, time, duration_mins FROM appointments WHERE doctor_id = :doc_id AND date = :appt_date ORDER BY time"), {"doc_id": doctor_id, "appt_date": appointment_date_obj}).fetchall()

    schedule = []
    for row in results:
        appt_id = row.id
        start_dt = datetime.combine(appointment_date_obj, row.time)
        duration = row.duration_mins
        schedule.append((appt_id, start_dt, duration))
    return schedule

def simulated_annealing(initial_schedule, initial_temp, min_temp, iterations, cool_rate):

    T = initial_temp
    schedule = initial_schedule.copy()
    best_schedule = schedule.copy()
    best_score = evaluate(schedule)

    while T > min_temp:
        #Main loop where new possible schedules are made and compared
        for _ in range(iterations):
            new_schedule = perturbate(schedule)
            new_score = evaluate(new_schedule)
            delta = new_score - best_score

            # Accept new schedule if better, or using a probability distribution if its worse
            if delta < 0 or rand.random() < np.exp(-delta / max(T, 1e-8)):
                schedule = new_schedule.copy()
                if new_score < best_score:
                    best_schedule = new_schedule.copy()
                    best_score = new_score

        T *= cool_rate
    return best_schedule

def evaluate(schedule):
    #Lower scores for better schedules, more overlaps are bad, earlier is better
    
    score = 0

    def get_start_time(appt):
        return appt[1]

    sorted_sch = sorted(schedule, key=get_start_time)
    work_start_dt = datetime.combine(sorted_sch[0][1].date(), work_start)
    work_end_dt = datetime.combine(sorted_sch[0][1].date(), work_end)

    for i, (appt_id, start, duration) in enumerate(sorted_sch):
        end = start + timedelta(minutes=duration)
        
        if start < work_start_dt or end > work_end_dt: #Anything out of bounds
            score += 10000

        if i > 0: #Overlaps
            prev_end = sorted_sch[i-1][1] + timedelta(minutes=sorted_sch[i-1][2])
            if start < prev_end:
                score += 10000
            gap = (start - prev_end).total_seconds() / 60
            score += gap
              #smaller gaps better

    last_end = sorted_sch[-1][1] + timedelta(minutes=sorted_sch[-1][2]) #late finishing

    score += (last_end - work_end_dt).total_seconds() / 3  #if past work hours

    score -= (work_end_dt - last_end).total_seconds() / 10 #early finish

    return score

def perturbate(schedule):
    #Shuffles order and start from the earliest start time or random time in interval
    
    sched = schedule.copy()
    if rand.random() < 0.5:
        rand.shuffle(sched)
        day = sched[0][1].date()
        current = datetime.combine(day, work_start)

        new_sched = []
        for appt_id, _, duration in sched:
            new_start = current
            new_sched.append((appt_id, new_start, duration))
            current = new_start + timedelta(minutes=duration)

        return new_sched
    else:

        day = sched[0][1].date()

        random_start = datetime.combine(day, time(rand.randint(8, 10), rand.choice([0, 15, 30, 45])))
        current = random_start
        rand.shuffle(sched)

        new_sched = []
        for appt_id, _, duration in sched:
            new_sched.append((appt_id, current, duration))
            current = current + timedelta(minutes=duration)

        return new_sched

def save_schedule_to_db(db, optimised_schedule):
    #Saves new schedule to the database

    
    for appt_id, start_dt, duration in optimised_schedule:
        db.session.execute(text("UPDATE appointments SET time = :new_time, duration_mins = :duration WHERE id = :appt_id"),{"new_time": start_dt.time(), "duration": duration, "appt_id": appt_id})
    db.session.commit()