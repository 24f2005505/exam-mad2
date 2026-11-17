from model import User, db, Student, Examiner, Course, Examination, Rubric, Slot, Booking
from werkzeug.security import generate_password_hash as ph
from flask import request, jsonify
from datetime import datetime
from restrict_access import restrict
from make_form import username_unique, email_unique
from view import course_view, examination_view, rubric_view, slot_view, booking_view, student_view, examiner_view, full_name
from utils import missing_fields, matches, refresh_slot, read_slot, slot_overlaps, EXAM_TYPES, EXAM_STATUSES
from cache import cache_get, cache_set, cache_clear



def get_dashboard_stats():
    stats = {}
    stats['total_courses'] = Course.query.count()
    stats['total_examinations'] = Examination.query.count()
    stats['total_students'] = Student.query.count()
    stats['total_examiners'] = Examiner.query.count()
    stats['total_slots'] = Slot.query.filter(Slot.status != "cancelled").count()
    stats['total_bookings'] = Booking.query.filter(Booking.status != "cancelled").count()
    return stats


############### seach functions ################
def search_for_courses(query):
    courses = Course.query.all()
    if query:
        courses = [c for c in courses if matches(query, c.id, c.course_code, c.course_name, c.description, c.status)]
    return courses

def search_for_examinations(query):
    exams = Examination.query.all()
    if query:
        exams = [e for e in exams if matches(query, e.id, e.examination_name, e.examination_type, e.status, e.course.course_code, e.course.course_name)]
    return exams

def search_for_examiners(query):
    examiners = Examiner.query.all()
    if query:
        examiners = [e for e in examiners if matches(query, e.id, e.user.fname, e.user.lname, e.user.username, e.user.email, e.department)]
    return examiners

def search_for_students(query):
    students = Student.query.all()
    if query:
        students = [s for s in students if matches(query, s.id, s.user.fname, s.user.lname, s.user.username, s.user.email, s.university, s.major)]
    return students

def search_for_bookings(query):
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    if query:
        bookings = [b for b in bookings if matches(query, b.id, b.student.user.fname, b.student.user.lname, b.student.user.email,
                                                   b.examination.examination_name, b.examination.course.course_code,
                                                   b.slot.examiner.user.fname, b.slot.examiner.user.lname, b.status)]
    return bookings


############### read form functions (check the data sent by vue) ################
def read_course(data, course_id=None):
    missing = missing_fields(data, ["course_code", "course_name", "description"])
    if missing:
        return None, f"Please fill the {missing}."
    code = data["course_code"].strip().upper()
    other = Course.query.filter_by(course_code=code).first()
    if other and other.id != course_id:
        return None, "A course with this code already exists."
    status = data.get("status") or "active"
    if status not in ("active", "inactive"):
        return None, "Invalid course status."
    return {"course_code": code, "course_name": data["course_name"].strip(), "description": data["description"].strip(), "status": status}, None


def read_examination(data):
    missing = missing_fields(data, ["course_id", "examination_name", "examination_type", "duration", "maximum_marks",
                                    "slot_creation_start", "slot_creation_end", "slot_booking_start", "slot_booking_end"])
    if missing:
        return None, f"Please fill the {missing}."
    if data["examination_type"] not in EXAM_TYPES:
        return None, "Invalid examination type."
    try:
        values = {
            "course_id": int(data["course_id"]),
            "examination_name": data["examination_name"].strip(),
            "examination_type": data["examination_type"],
            "duration": int(data["duration"]),
            "maximum_marks": float(data["maximum_marks"]),
            "slot_creation_start": datetime.fromisoformat(data["slot_creation_start"]),
            "slot_creation_end": datetime.fromisoformat(data["slot_creation_end"]),
            "slot_booking_start": datetime.fromisoformat(data["slot_booking_start"]),
            "slot_booking_end": datetime.fromisoformat(data["slot_booking_end"]),
            "instructions": (data.get("instructions") or "").strip()
        }
    except ValueError:
        return None, "Please check the numbers and dates."
    if db.session.get(Course, values["course_id"]) is None:
        return None, "Course not found."
    if values["duration"] <= 0 or values["maximum_marks"] <= 0:
        return None, "Duration and maximum marks must be more than 0."
    if values["slot_creation_start"] >= values["slot_creation_end"]:
        return None, "Slot creation must end after it starts."
    if values["slot_booking_start"] >= values["slot_booking_end"]:
        return None, "Slot booking must end after it starts."
    if values["slot_creation_end"] > values["slot_booking_start"]:
        return None, "Slot booking can only start after slot creation ends."
    return values, None


def rubric_total(exam, skip_rubric_id=None):
    return sum(r.maximum_marks * r.weightage for r in exam.rubrics if r.id != skip_rubric_id)


def read_rubric(data, exam, rubric_id=None):
    missing = missing_fields(data, ["criterion_name", "maximum_marks"])
    if missing:
        return None, f"Please fill the {missing}."
    try:
        maximum_marks = float(data["maximum_marks"])
        weightage = float(data.get("weightage") or 1)
    except ValueError:
        return None, "Marks and weightage must be numbers."
    if maximum_marks <= 0 or weightage <= 0:
        return None, "Marks and weightage must be more than 0."
    ## total marks of the rubric (marks x weightage) can not go above the examination maximum marks
    new_total = rubric_total(exam, rubric_id) + maximum_marks * weightage
    if new_total > exam.maximum_marks:
        return None, f"Rubric total ({new_total:g}) can not be more than the examination maximum marks ({exam.maximum_marks:g})."
    return {"criterion_name": data["criterion_name"].strip(), "maximum_marks": maximum_marks,
            "weightage": weightage, "description": (data.get("description") or "").strip()}, None


def get_rubrics(exam):
    ## rubrics are cached in redis
    rubrics = cache_get(f"examination:{exam.id}:rubrics")
    if rubrics is None:
        rubrics = [rubric_view(r) for r in exam.rubrics]
        cache_set(f"examination:{exam.id}:rubrics", rubrics)
    return rubrics


def get_report():
    exams = []
    for exam in Examination.query.all():
        active = [b for b in exam.bookings if b.status != "cancelled"]
        evaluated = [b for b in active if b.evaluation]
        average = round(sum(b.evaluation.total_marks for b in evaluated) / len(evaluated), 2) if evaluated else None
        exams.append({
            "id": exam.id,
            "examination_name": exam.examination_name,
            "course_code": exam.course.course_code,
            "status": exam.status,
            "results_published": exam.results_published,
            "total_slots": len([s for s in exam.slots if s.status != "cancelled"]),
            "total_bookings": len(active),
            "evaluated": len(evaluated),
            "average_marks": average,
            "maximum_marks": exam.maximum_marks
        })
    examiners = []
    for examiner in Examiner.query.all():
        bookings = [b for s in examiner.slots for b in s.bookings if b.status != "cancelled"]
        examiners.append({
            "id": examiner.id,
            "name": full_name(examiner.user),
            "department": examiner.department,
            "total_slots": len([s for s in examiner.slots if s.status != "cancelled"]),
            "booked_students": len(bookings),
            "evaluations_done": len(examiner.evaluations),
            "pending_evaluations": len([b for b in bookings if b.status == "booked"])
        })
    return {"stats": get_dashboard_stats(), "examinations": exams, "examiners": examiners}



################# main function ################
def make_dashboard(app):

    @app.route('/api/admin/dashboard')
    @restrict("admin")
    def admin_dashboard():
        return jsonify(get_dashboard_stats())


    ################# courses #################
    @app.route('/api/admin/course', methods = ["GET", "POST"])
    @restrict("admin")
    def admin_course():
        if request.method == "POST":
            values, error = read_course(request.get_json())
            if error:
                return jsonify(error=error), 400
            db.session.add(Course(**values))
            db.session.commit()
            cache_clear()
            return jsonify(message="Course added successfully!"), 201
        query = request.args.get("query", "")
        return jsonify(courses=[course_view(c) for c in search_for_courses(query)])


    @app.route('/api/admin/course/<int:course_id>', methods = ["PUT", "DELETE"])
    @restrict("admin")
    def admin_edit_course(course_id):
        course = db.session.get(Course, course_id)
        if course is None:
            return jsonify(error="Course not found."), 404
        if request.method == "DELETE":
            if course.examinations:
                return jsonify(error="This course has examinations. Delete them first."), 400
            db.session.delete(course)
            db.session.commit()
            cache_clear()
            return jsonify(message="Course deleted.")
        values, error = read_course(request.get_json(), course.id)
        if error:
            return jsonify(error=error), 400
        for key, value in values.items():
            setattr(course, key, value)
        db.session.commit()
        cache_clear()
        return jsonify(message="Course updated successfully!")


    ################# examinations #################
    @app.route('/api/admin/examination', methods = ["GET", "POST"])
    @restrict("admin")
    def admin_examination():
        if request.method == "POST":
            values, error = read_examination(request.get_json())
            if error:
                return jsonify(error=error), 400
            db.session.add(Examination(**values, status="draft"))
            db.session.commit()
            cache_clear()
            return jsonify(message="Examination added successfully! It is in draft, open slot creation when ready."), 201
        query = request.args.get("query", "")
        return jsonify(examinations=[examination_view(e) for e in search_for_examinations(query)])


    @app.route('/api/admin/examination/<int:exam_id>', methods = ["PUT", "DELETE"])
    @restrict("admin")
    def admin_edit_examination(exam_id):
        exam = db.session.get(Examination, exam_id)
        if exam is None:
            return jsonify(error="Examination not found."), 404
        if request.method == "DELETE":
            if exam.bookings:
                return jsonify(error="Students have booked this examination, it can not be deleted. Close it instead."), 400
            for rubric in exam.rubrics:
                db.session.delete(rubric)
            for slot in exam.slots:
                db.session.delete(slot)
            exam.examiners = []
            db.session.delete(exam)
            db.session.commit()
            cache_clear()
            return jsonify(message="Examination deleted.")
        values, error = read_examination(request.get_json())
        if error:
            return jsonify(error=error), 400
        if rubric_total(exam) > values["maximum_marks"]:
            return jsonify(error="Maximum marks can not be less than the rubric total."), 400
        for key, value in values.items():
            setattr(exam, key, value)
        db.session.commit()
        cache_clear()
        return jsonify(message="Examination updated successfully!")


    @app.route('/api/admin/examination/<int:exam_id>/status', methods = ["POST"])
    @restrict("admin")
    def admin_examination_status(exam_id):
        ## this is how admin opens / closes slot creation and slot booking
        exam = db.session.get(Examination, exam_id)
        if exam is None:
            return jsonify(error="Examination not found."), 404
        status = request.get_json().get("status")
        if status not in EXAM_STATUSES:
            return jsonify(error="Invalid status."), 400
        exam.status = status
        db.session.commit()
        cache_clear()
        return jsonify(message=f"{exam.examination_name} is now {status.replace('_', ' ')}.")


    @app.route('/api/admin/examination/<int:exam_id>/examiners', methods = ["POST"])
    @restrict("admin")
    def admin_examination_examiners(exam_id):
        exam = db.session.get(Examination, exam_id)
        if exam is None:
            return jsonify(error="Examination not found."), 404
        examiner_ids = [int(i) for i in request.get_json().get("examiner_ids", [])]
        exam.examiners = Examiner.query.filter(Examiner.id.in_(examiner_ids)).all()
        db.session.commit()
        cache_clear()
        return jsonify(message="Examiners assigned successfully!")


    @app.route('/api/admin/examination/<int:exam_id>/publish', methods = ["POST"])
    @restrict("admin")
    def admin_examination_publish(exam_id):
        exam = db.session.get(Examination, exam_id)
        if exam is None:
            return jsonify(error="Examination not found."), 404
        exam.results_published = bool(request.get_json().get("publish"))
        db.session.commit()
        cache_clear()
        return jsonify(message="Results published!" if exam.results_published else "Results hidden from students.")


    ################# rubrics #################
    @app.route('/api/admin/examination/<int:exam_id>/rubric', methods = ["GET", "POST"])
    @restrict("admin")
    def admin_rubric(exam_id):
        exam = db.session.get(Examination, exam_id)
        if exam is None:
            return jsonify(error="Examination not found."), 404
        if request.method == "POST":
            values, error = read_rubric(request.get_json(), exam)
            if error:
                return jsonify(error=error), 400
            db.session.add(Rubric(examination_id=exam.id, **values))
            db.session.commit()
            cache_clear()
            return jsonify(message="Rubric criterion added!"), 201
        return jsonify(rubrics=get_rubrics(exam), total=rubric_total(exam), maximum_marks=exam.maximum_marks)


    @app.route('/api/admin/rubric/<int:rubric_id>', methods = ["PUT", "DELETE"])
    @restrict("admin")
    def admin_edit_rubric(rubric_id):
        rubric = db.session.get(Rubric, rubric_id)
        if rubric is None:
            return jsonify(error="Rubric not found."), 404
        exam = rubric.examination
        if any(b.evaluation for b in exam.bookings):
            return jsonify(error="Students are already evaluated with this rubric, it can not be changed."), 400
        if request.method == "DELETE":
            db.session.delete(rubric)
            db.session.commit()
            cache_clear()
            return jsonify(message="Rubric criterion deleted.")
        values, error = read_rubric(request.get_json(), exam, rubric.id)
        if error:
            return jsonify(error=error), 400
        for key, value in values.items():
            setattr(rubric, key, value)
        db.session.commit()
        cache_clear()
        return jsonify(message="Rubric criterion updated!")


    ################# examiners #################
    @app.route('/api/admin/examiner', methods = ["GET", "POST"])
    @restrict("admin")
    def admin_examiner():
        if request.method == "POST":
            ## admin adds a new examiner (examiners can not register themselves)
            data = request.get_json()
            missing = missing_fields(data, ["fname", "lname", "username", "email", "password", "department", "contact_details"])
            if missing:
                return jsonify(error=f"Please fill the {missing}."), 400
            if not username_unique(User, data["username"]):
                return jsonify(error="Username already taken, please choose another one."), 409
            elif not email_unique(User, data["email"]):
                return jsonify(error="This email is registered."), 409

            user = User(
                    username= data["username"],
                    email= data["email"],
                    role = "examiner",
                    fname = data["fname"],
                    lname = data["lname"],
                    pwd_hash = ph(data["password"]),
                    gender = "other",
                    admin_approval_status = "approved"
                )
            db.session.add(user)
            db.session.flush()

            examiner = Examiner(
                eid = user.id,
                department = data["department"],
                contact_details = data["contact_details"]
            )
            db.session.add(examiner)
            db.session.commit()
            return jsonify(message="Examiner added successfully!"), 201

        query = request.args.get("query", "")
        return jsonify(examiners=[examiner_view(e) for e in search_for_examiners(query)])


    @app.route('/api/admin/examiner/<int:examiner_id>', methods = ["PUT"])
    @restrict("admin")
    def admin_edit_examiner(examiner_id):
        examiner = db.session.get(Examiner, examiner_id)
        if examiner is None:
            return jsonify(error="Examiner not found."), 404
        data = request.get_json()
        missing = missing_fields(data, ["fname", "lname", "email", "department", "contact_details", "status"])
        if missing:
            return jsonify(error=f"Please fill the {missing}."), 400
        other = User.query.filter_by(email=data["email"]).first()
        if other and other.id != examiner.eid:
            return jsonify(error="This email is registered."), 409
        if data["status"] not in ("active", "inactive"):
            return jsonify(error="Invalid status."), 400
        examiner.user.fname = data["fname"]
        examiner.user.lname = data["lname"]
        examiner.user.email = data["email"]
        examiner.department = data["department"]
        examiner.contact_details = data["contact_details"]
        examiner.status = data["status"]
        db.session.commit()
        cache_clear()
        return jsonify(message="Examiner updated successfully!")


    ################# students #################
    @app.route('/api/admin/student')
    @restrict("admin")
    def admin_student():
        query = request.args.get("query", "")
        return jsonify(students=[student_view(s) for s in search_for_students(query)])


    @app.route('/api/admin/student/<int:student_id>/ban', methods = ["POST"])
    @restrict("admin")
    def admin_ban_student(student_id):
        student = db.session.get(Student, student_id)
        if student is None:
            return jsonify(error="Student not found."), 404
        student.user.admin_enforced_blacklist_status = bool(request.get_json().get("ban"))
        db.session.commit()
        return jsonify(message="Student banned." if student.user.admin_enforced_blacklist_status else "Student unbanned.")


    ################# slots #################
    @app.route('/api/admin/slot')
    @restrict("admin")
    def admin_slot():
        slots = Slot.query.order_by(Slot.date, Slot.start_time).all()
        exam_id = request.args.get("examination_id", type=int)
        if exam_id:
            slots = [s for s in slots if s.examination_id == exam_id]
        return jsonify(slots=[slot_view(s) for s in slots])


    @app.route('/api/admin/slot/<int:slot_id>', methods = ["PUT"])
    @restrict("admin")
    def admin_reschedule_slot(slot_id):
        ## admin can reschedule a slot and change its examiner in exceptional situations
        slot = db.session.get(Slot, slot_id)
        if slot is None:
            return jsonify(error="Slot not found."), 404
        if slot.status == "cancelled":
            return jsonify(error="This slot is cancelled."), 400
        data = request.get_json()
        values, error = read_slot(data)
        if error:
            return jsonify(error=error), 400
        examiner = db.session.get(Examiner, int(data.get("examiner_id") or 0))
        if examiner is None:
            return jsonify(error="Please choose an examiner."), 400
        taken = slot.max_student_capacity - slot.available_seats
        if values["max_student_capacity"] < taken:
            return jsonify(error=f"{taken} students already booked this slot, capacity can not be less than that."), 400
        if slot_overlaps(examiner.id, values["date"], values["start_time"], values["end_time"], slot.id):
            return jsonify(error="This examiner already has a slot at that time."), 400
        if examiner not in slot.examination.examiners:
            slot.examination.examiners.append(examiner)
        for key, value in values.items():
            setattr(slot, key, value)
        slot.examiner_id = examiner.id
        refresh_slot(slot)
        db.session.commit()
        cache_clear()
        return jsonify(message="Slot rescheduled successfully!")


    @app.route('/api/admin/slot/<int:slot_id>/cancel', methods = ["POST"])
    @restrict("admin")
    def admin_cancel_slot(slot_id):
        slot = db.session.get(Slot, slot_id)
        if slot is None:
            return jsonify(error="Slot not found."), 404
        if any(b.status == "completed" for b in slot.bookings):
            return jsonify(error="Students in this slot are already evaluated, it can not be cancelled."), 400
        for booking in slot.bookings:
            if booking.status == "booked":
                booking.status = "cancelled"  ## students can book another slot again
        slot.status = "cancelled"
        refresh_slot(slot)
        db.session.commit()
        cache_clear()
        return jsonify(message="Slot cancelled. Its bookings were cancelled too.")


    ################# bookings #################
    @app.route('/api/admin/booking')
    @restrict("admin")
    def admin_booking():
        query = request.args.get("query", "")
        return jsonify(bookings=[booking_view(b) for b in search_for_bookings(query)])


    @app.route('/api/admin/booking/<int:booking_id>/reschedule', methods = ["POST"])
    @restrict("admin")
    def admin_reschedule_booking(booking_id):
        ## move a student to another slot (this also reassigns the student to that slot's examiner)
        booking = db.session.get(Booking, booking_id)
        if booking is None:
            return jsonify(error="Booking not found."), 404
        if booking.status != "booked":
            return jsonify(error="Only booked (not cancelled or completed) bookings can be rescheduled."), 400
        new_slot = db.session.get(Slot, int(request.get_json().get("slot_id") or 0))
        if new_slot is None or new_slot.examination_id != booking.examination_id:
            return jsonify(error="Please choose a slot of the same examination."), 400
        if new_slot.id == booking.slot_id:
            return jsonify(error="The student is already in this slot."), 400
        if new_slot.status != "available" or new_slot.available_seats <= 0:
            return jsonify(error="That slot is full or not available."), 400
        old_slot = booking.slot
        booking.slot_id = new_slot.id
        db.session.flush()
        refresh_slot(old_slot)
        refresh_slot(new_slot)
        db.session.commit()
        cache_clear()
        return jsonify(message="Booking rescheduled successfully!")


    ################# reports #################
    @app.route('/api/admin/report')
    @restrict("admin")
    def admin_report():
        return jsonify(get_report())
