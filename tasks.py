## celery jobs: daily reminder, monthly report, csv export
import csv
import os
from collections import Counter
from datetime import date, datetime, time, timedelta
from make_celery import celery
from model import db, User, Student, Slot, Booking, Evaluation
from view import full_name
from mailer import send_email, send_gchat


def flask_app():
    from app import app  ## imported here (not at the top) so app.py and tasks.py do not import each other in a loop
    return app


################# a. daily examination reminder #################
@celery.task
def daily_reminder():
    with flask_app().app_context():
        today = date.today()
        tomorrow = today + timedelta(days=1)
        bookings = Booking.query.join(Slot).filter(Booking.status == "booked", Slot.status != "cancelled",
                                                   Slot.date >= today, Slot.date <= tomorrow).all()
        sent = 0
        for booking in bookings:
            exam = booking.examination
            slot = booking.slot
            user = booking.student.user
            examiner = full_name(slot.examiner.user)
            html = f'''
            <h2>Examination Reminder</h2>
            <p>Hi {user.fname},</p>
            <p>This is a reminder for your upcoming examination.</p>
            <table border="1" cellpadding="6" cellspacing="0">
                <tr><td><b>Examination</b></td><td>{exam.examination_name} ({exam.course.course_code})</td></tr>
                <tr><td><b>Date</b></td><td>{slot.date:%d %b %Y}</td></tr>
                <tr><td><b>Time</b></td><td>{slot.start_time:%H:%M} - {slot.end_time:%H:%M}</td></tr>
                <tr><td><b>Examiner</b></td><td>{examiner}</td></tr>
                <tr><td><b>Meeting Link</b></td><td>{slot.meeting_link or "Not given"}</td></tr>
                <tr><td><b>Instructions</b></td><td>{exam.instructions or "No instructions"}</td></tr>
            </table>
            <p>All the best!</p>
            '''
            try:
                send_email(user.email, f"Reminder: {exam.examination_name} on {slot.date:%d %b %Y}", html)
                send_gchat(f"Reminder for {user.fname}: {exam.examination_name} on {slot.date:%d %b %Y} "
                           f"at {slot.start_time:%H:%M} with {examiner}. Instructions: {exam.instructions or 'none'}")
                sent += 1
            except Exception as e:
                print("Could not send reminder to", user.email, e)
        return f"Sent {sent} of {len(bookings)} reminders."


################# b. monthly examination report #################
def make_monthly_report():
    first_of_this_month = date.today().replace(day=1)
    start = (first_of_this_month - timedelta(days=1)).replace(day=1)  ## first day of last month
    start_time = datetime.combine(start, time.min)
    end_time = datetime.combine(first_of_this_month, time.min)

    evaluations = Evaluation.query.filter(Evaluation.evaluation_date >= start_time, Evaluation.evaluation_date < end_time).all()
    month_slots = Slot.query.filter(Slot.date >= start, Slot.date < first_of_this_month).all()

    exams_conducted = {s.examination_id for s in month_slots if s.status == "completed"} | {e.booking.examination_id for e in evaluations}
    students_evaluated = {e.booking.student_id for e in evaluations}
    completed_bookings = Booking.query.join(Slot).filter(Booking.status == "completed", Slot.date >= start, Slot.date < first_of_this_month).count()
    pending_evaluations = Booking.query.join(Slot).filter(Booking.status == "booked", Slot.date < date.today()).count()
    active_examiners = Counter(full_name(e.examiner.user) for e in evaluations).most_common(5)

    examiner_rows = "".join(f"<tr><td>{name}</td><td>{count}</td></tr>" for name, count in active_examiners)
    if not examiner_rows:
        examiner_rows = '<tr><td colspan="2">No evaluations this month.</td></tr>'

    html = f'''
    <h2>Monthly Examination Report - {start:%B %Y}</h2>
    <table border="1" cellpadding="6" cellspacing="0">
        <tr><td><b>Examinations conducted</b></td><td>{len(exams_conducted)}</td></tr>
        <tr><td><b>Students evaluated</b></td><td>{len(students_evaluated)}</td></tr>
        <tr><td><b>Completed bookings</b></td><td>{completed_bookings}</td></tr>
        <tr><td><b>Pending evaluations (till today)</b></td><td>{pending_evaluations}</td></tr>
    </table>
    <h3>Most active examiners</h3>
    <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>Examiner</th><th>Evaluations</th></tr>
        {examiner_rows}
    </table>
    '''
    return f"Monthly Examination Report - {start:%B %Y}", html


@celery.task
def monthly_report():
    with flask_app().app_context():
        subject, html = make_monthly_report()
        for admin in User.query.filter_by(role="admin").all():
            send_email(admin.email, subject, html)
        return subject + " sent."


################# c. export examination history as csv (user triggered) #################
@celery.task(bind=True)
def export_history(self, student_id):
    app = flask_app()
    with app.app_context():
        student = db.session.get(Student, student_id)
        folder = os.path.join(app.root_path, "exports")
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"history_{student_id}_{self.request.id}.csv")

        with open(file_path + ".tmp", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Student ID", "Examination Name", "Course", "Examination Date", "Examiner", "Marks Obtained", "Booking Status"])
            for booking in student.bookings:
                exam = booking.examination
                if booking.evaluation and exam.results_published:
                    marks = booking.evaluation.total_marks
                else:
                    marks = "Not published"
                writer.writerow([student.id, exam.examination_name, exam.course.course_code + " - " + exam.course.course_name,
                                 booking.slot.date.isoformat(), full_name(booking.slot.examiner.user), marks, booking.status])
        os.replace(file_path + ".tmp", file_path)  ## rename at the end so the file only shows up when it is complete
        return file_path
