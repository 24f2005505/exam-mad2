from flask import request, jsonify, send_file
from flask_login import current_user
from datetime import datetime, date
import os
import uuid
from model import db, User, Examination, Slot, Booking
from restrict_access import restrict
from view import examination_view, slot_view, booking_view, student_view
from utils import matches, missing_fields, booking_is_open, refresh_slot
from werkzeug.security import generate_password_hash as ph
from cache import cache_get, cache_set, cache_clear, redis_available
from tasks import export_history


def get_dashboard_stats():
    student = current_user.student
    today = date.today()
    open_exams = [e for e in Examination.query.all() if booking_is_open(e) and e.course.status == "active"]
    stats = {}
    stats['my_name'] = current_user.fname + " " + current_user.lname
    stats['my_university'] = student.university
    stats['available_examinations'] = len(open_exams)
    stats['available_slots'] = sum(len([s for s in e.slots if s.status == "available" and s.date >= today]) for e in open_exams)
    stats['upcoming_examinations'] = len([b for b in student.bookings if b.status == "booked" and b.slot.date >= today])
    stats['booked_slots'] = len([b for b in student.bookings if b.status == "booked"])
    stats['published_results'] = len([b for b in student.bookings if b.evaluation and b.examination.results_published])
    return stats


def get_examination_list():
    ## frequently accessed examinations are cached in redis
    exams = cache_get("examinations")
    if exams is None:
        exams = [examination_view(e) for e in Examination.query.all() if e.status != "draft" and e.course.status == "active"]
        cache_set("examinations", exams)
    return exams


def get_examination_slots(exam):
    ## examination schedule (its slots) is cached in redis, for 1 minute because seats change often
    slots = cache_get(f"examination:{exam.id}:slots")
    if slots is None:
        slots = [slot_view(s) for s in sorted(exam.slots, key=lambda s: (s.date, s.start_time)) if s.status != "cancelled"]
        cache_set(f"examination:{exam.id}:slots", slots, 60)
    return slots


def export_file_path(app, task_id):
    return os.path.join(app.root_path, "exports", f"history_{current_user.student.id}_{task_id}.csv")


################# main function ################
def make_dashboard(app):

    @app.route('/api/student/dashboard')
    @restrict("student")
    def student_dashboard():
        today = date.today()
        bookings = sorted(current_user.student.bookings, key=lambda b: (b.slot.date, b.slot.start_time))
        upcoming = [booking_view(b, True) for b in bookings if b.status == "booked" and b.slot.date >= today]
        results = [booking_view(b, True) for b in bookings if b.evaluation and b.examination.results_published]
        return jsonify(stats=get_dashboard_stats(), upcoming=upcoming, results=results)


    ################# examinations #################
    @app.route('/api/student/examination')
    @restrict("student")
    def student_examination():
        query = request.args.get("query", "")
        exam_type = request.args.get("type", "")
        course_id = request.args.get("course_id", type=int)
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")

        my_status = {b.examination_id: b.status for b in current_user.student.bookings}
        exams = []
        for exam in get_examination_list():
            if query and not matches(query, exam["examination_name"], exam["course_code"], exam["course_name"]):
                continue
            if exam_type and exam["examination_type"] != exam_type:
                continue
            if course_id and exam["course_id"] != course_id:
                continue
            exam = dict(exam)
            ## dates are "YYYY-MM-DDTHH:MM" strings so they can be compared directly
            exam["booking_open"] = exam["status"] == "booking_open" and exam["slot_booking_start"] <= now <= exam["slot_booking_end"]
            exam["my_booking"] = my_status.get(exam["id"])
            exams.append(exam)

        courses = {}
        for exam in get_examination_list():
            courses[exam["course_id"]] = exam["course_code"] + " - " + exam["course_name"]
        return jsonify(examinations=exams, courses=[{"id": k, "name": v} for k, v in courses.items()])


    @app.route('/api/student/examination/<int:exam_id>/slots')
    @restrict("student")
    def student_examination_slots(exam_id):
        exam = db.session.get(Examination, exam_id)
        if exam is None or exam.status == "draft":
            return jsonify(error="Examination not found."), 404
        return jsonify(slots=get_examination_slots(exam), booking_open=booking_is_open(exam))


    ################# bookings #################
    @app.route('/api/student/book', methods = ["POST"])
    @restrict("student")
    def student_book():
        student = current_user.student
        slot = db.session.get(Slot, int(request.get_json().get("slot_id") or 0))
        if slot is None:
            return jsonify(error="Slot not found."), 404
        exam = slot.examination
        if not booking_is_open(exam):
            return jsonify(error=f"Booking is not open. Booking period: {exam.slot_booking_start:%d %b %Y %H:%M} to {exam.slot_booking_end:%d %b %Y %H:%M}."), 400
        if slot.status != "available" or slot.available_seats <= 0:
            return jsonify(error="This slot is full or not available."), 400
        if slot.date < date.today():
            return jsonify(error="This slot is in the past."), 400

        ## one slot per examination, no duplicate bookings
        booking = Booking.query.filter_by(student_id=student.id, examination_id=exam.id).first()
        if booking and booking.status != "cancelled":
            return jsonify(error="You have already booked a slot for this examination."), 400
        if booking:
            ## re-use the cancelled booking (one booking row per student per examination)
            booking.slot_id = slot.id
            booking.status = "booked"
            booking.booking_date = datetime.now()
        else:
            booking = Booking(student_id=student.id, examination_id=exam.id, slot_id=slot.id, booking_date=datetime.now(), status="booked")
            db.session.add(booking)
        db.session.flush()
        refresh_slot(slot)  ## marks the slot full when capacity is reached
        db.session.commit()
        cache_clear()
        return jsonify(message=f"Slot booked for {exam.examination_name} on {slot.date:%d %b %Y} at {slot.start_time:%H:%M}!")


    @app.route('/api/student/booking/<int:booking_id>/cancel', methods = ["POST"])
    @restrict("student")
    def student_cancel_booking(booking_id):
        booking = db.session.get(Booking, booking_id)
        if booking is None or booking.student_id != current_user.student.id:
            return jsonify(error="Booking not found."), 404
        if booking.status != "booked":
            return jsonify(error="Only booked slots can be cancelled."), 400
        if datetime.now() >= booking.examination.slot_booking_end:
            return jsonify(error="The booking deadline has passed, this booking can not be cancelled."), 400
        booking.status = "cancelled"
        db.session.flush()
        refresh_slot(booking.slot)
        db.session.commit()
        cache_clear()
        return jsonify(message="Booking cancelled.")


    @app.route('/api/student/booking')
    @restrict("student")
    def student_booking():
        bookings = sorted(current_user.student.bookings, key=lambda b: b.booking_date, reverse=True)
        return jsonify(bookings=[booking_view(b, True) for b in bookings])


    ################# profile #################
    @app.route('/api/student/profile', methods = ["GET", "PUT"])
    @restrict("student")
    def student_profile():
        student = current_user.student
        if request.method == "PUT":
            data = request.get_json()
            missing = missing_fields(data, ["fname", "lname", "email", "university", "major", "gpa"])
            if missing:
                return jsonify(error=f"Please fill the {missing}."), 400
            other = User.query.filter_by(email=data["email"]).first()
            if other and other.id != current_user.id:
                return jsonify(error="This email is registered."), 409
            if data.get("password"):
                if data["password"] != data.get("con_password"):
                    return jsonify(error="Passwords do not match, please re-enter."), 400
                current_user.pwd_hash = ph(data["password"])
            current_user.fname = data["fname"]
            current_user.lname = data["lname"]
            current_user.email = data["email"]
            student.university = data["university"]
            student.major = data["major"]
            student.gpa = data["gpa"]
            db.session.commit()
            return jsonify(message="Profile updated successfully!", profile=student_view(student))
        return jsonify(profile=student_view(student))


    ################# export history as csv (celery) #################
    @app.route('/api/student/export', methods = ["POST"])
    @restrict("student")
    def student_export():
        if not redis_available():
            return jsonify(error="Could not start the export. Make sure Redis and the Celery worker are running."), 503
        try:
            task = export_history.delay(current_user.student.id)
        except Exception:
            return jsonify(error="Could not start the export. Make sure Redis and the Celery worker are running."), 503
        return jsonify(message="Export started. You will get an alert when it is ready.", task_id=task.id)


    @app.route('/api/student/export/<task_id>')
    @restrict("student")
    def student_export_status(task_id):
        try:
            uuid.UUID(task_id)
        except ValueError:
            return jsonify(error="Invalid export id."), 400
        return jsonify(ready=os.path.exists(export_file_path(app, task_id)))


    @app.route('/api/student/export/<task_id>/download')
    @restrict("student")
    def student_export_download(task_id):
        try:
            uuid.UUID(task_id)
        except ValueError:
            return jsonify(error="Invalid export id."), 400
        file_path = export_file_path(app, task_id)  ## the file name has the student id, so students only get their own file
        if not os.path.exists(file_path):
            return jsonify(error="Export not ready yet."), 404
        return send_file(file_path, as_attachment=True, download_name="examination_history.csv")
