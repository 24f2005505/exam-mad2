from flask import request, jsonify
from flask_login import current_user
from datetime import datetime
from model import db, Slot, Booking, Evaluation
from restrict_access import restrict
from view import examination_view, slot_view, booking_view
from utils import read_slot, slot_overlaps, refresh_slot, slot_creation_is_open, slots_can_be_changed
from make_admin_dashboard import get_rubrics
from cache import cache_clear


def my_bookings(examiner):
    ## all (not cancelled) bookings in this examiner's slots
    return [b for s in examiner.slots for b in s.bookings if b.status != "cancelled"]


def get_dashboard_stats():
    examiner = current_user.examiner
    bookings = my_bookings(examiner)
    stats = {}
    stats['my_name'] = current_user.fname + " " + current_user.lname
    stats['my_department'] = examiner.department
    stats['assigned_examinations'] = len(examiner.examinations)
    stats['created_slots'] = len([s for s in examiner.slots if s.status != "cancelled"])
    stats['booked_students'] = len(bookings)
    stats['pending_evaluations'] = len([b for b in bookings if b.status == "booked"])
    return stats


def examination_for_examiner(exam):
    data = examination_view(exam)
    data["can_create_slots"] = slot_creation_is_open(exam)
    data["can_change_slots"] = slots_can_be_changed(exam)
    return data


def get_my_slot(slot_id):
    ## examiners can only touch their own slots
    slot = db.session.get(Slot, slot_id)
    if slot is None or slot.examiner_id != current_user.examiner.id:
        return None
    return slot


def get_my_booking(booking_id):
    ## examiners can only evaluate students booked into their slots
    booking = db.session.get(Booking, booking_id)
    if booking is None or booking.slot.examiner_id != current_user.examiner.id or booking.status == "cancelled":
        return None
    return booking


################# main function ################
def make_dashboard(app):

    @app.route('/api/examiner/dashboard')
    @restrict("examiner")
    def examiner_dashboard():
        exams = [examination_for_examiner(e) for e in current_user.examiner.examinations]
        return jsonify(stats=get_dashboard_stats(), examinations=exams)


    @app.route('/api/examiner/examination')
    @restrict("examiner")
    def examiner_examination():
        return jsonify(examinations=[examination_for_examiner(e) for e in current_user.examiner.examinations])


    ################# slots #################
    @app.route('/api/examiner/slot', methods = ["GET", "POST"])
    @restrict("examiner")
    def examiner_slot():
        examiner = current_user.examiner
        if request.method == "POST":
            data = request.get_json()
            exam = next((e for e in examiner.examinations if e.id == int(data.get("examination_id") or 0)), None)
            if exam is None:
                return jsonify(error="You are not assigned to this examination."), 403
            if not slot_creation_is_open(exam):
                return jsonify(error=f"Slots can only be created while slot creation is open ({exam.slot_creation_start:%d %b %Y %H:%M} to {exam.slot_creation_end:%d %b %Y %H:%M})."), 400
            values, error = read_slot(data)
            if error:
                return jsonify(error=error), 400
            if slot_overlaps(examiner.id, values["date"], values["start_time"], values["end_time"]):
                return jsonify(error="You already have a slot at that time."), 400
            if values["date"] < exam.slot_booking_start.date():
                return jsonify(error="The slot date must be after slot booking starts."), 400
            slot = Slot(examination_id=exam.id, examiner_id=examiner.id, available_seats=values["max_student_capacity"], status="available", **values)
            db.session.add(slot)
            db.session.commit()
            cache_clear()
            return jsonify(message="Slot created successfully!"), 201

        slots = sorted(examiner.slots, key=lambda s: (s.date, s.start_time))
        data = []
        for slot in slots:
            view = slot_view(slot)
            view["can_change"] = slots_can_be_changed(slot.examination) and not slot.bookings and slot.status != "cancelled"
            data.append(view)
        return jsonify(slots=data)


    @app.route('/api/examiner/slot/<int:slot_id>', methods = ["PUT", "DELETE"])
    @restrict("examiner")
    def examiner_edit_slot(slot_id):
        slot = get_my_slot(slot_id)
        if slot is None:
            return jsonify(error="Slot not found."), 404
        if not slots_can_be_changed(slot.examination) or slot.bookings:
            return jsonify(error="Slots can only be updated or removed before student booking begins."), 400
        if request.method == "DELETE":
            db.session.delete(slot)
            db.session.commit()
            cache_clear()
            return jsonify(message="Slot removed.")
        values, error = read_slot(request.get_json())
        if error:
            return jsonify(error=error), 400
        if slot_overlaps(slot.examiner_id, values["date"], values["start_time"], values["end_time"], slot.id):
            return jsonify(error="You already have a slot at that time."), 400
        for key, value in values.items():
            setattr(slot, key, value)
        refresh_slot(slot)
        db.session.commit()
        cache_clear()
        return jsonify(message="Slot updated successfully!")


    @app.route('/api/examiner/slot/<int:slot_id>/complete', methods = ["POST"])
    @restrict("examiner")
    def examiner_complete_slot(slot_id):
        ## examiner marks the examination (their slot) as completed
        slot = get_my_slot(slot_id)
        if slot is None:
            return jsonify(error="Slot not found."), 404
        if slot.status == "cancelled":
            return jsonify(error="This slot is cancelled."), 400
        if any(b.status == "booked" for b in slot.bookings):
            return jsonify(error="Evaluate all students of this slot first."), 400
        slot.status = "completed"
        db.session.commit()
        cache_clear()
        return jsonify(message="Slot marked as completed.")


    @app.route('/api/examiner/slot/<int:slot_id>/students')
    @restrict("examiner")
    def examiner_slot_students(slot_id):
        slot = get_my_slot(slot_id)
        if slot is None:
            return jsonify(error="Slot not found."), 404
        bookings = [booking_view(b) for b in slot.bookings if b.status != "cancelled"]
        return jsonify(slot=slot_view(slot), bookings=bookings)


    ################# evaluations #################
    @app.route('/api/examiner/evaluation')
    @restrict("examiner")
    def examiner_evaluation():
        bookings = my_bookings(current_user.examiner)
        bookings = sorted(bookings, key=lambda b: (b.slot.date, b.slot.start_time))
        pending = [booking_view(b) for b in bookings if b.status == "booked"]
        done = [booking_view(b) for b in bookings if b.status == "completed"]
        return jsonify(pending=pending, done=done)


    @app.route('/api/examiner/booking/<int:booking_id>/evaluate', methods = ["GET", "POST"])
    @restrict("examiner")
    def examiner_evaluate(booking_id):
        booking = get_my_booking(booking_id)
        if booking is None:
            return jsonify(error="Booking not found."), 404
        exam = booking.examination
        rubrics = get_rubrics(exam)
        if request.method == "GET":
            return jsonify(booking=booking_view(booking), rubrics=rubrics)

        if not rubrics:
            return jsonify(error="Admin has not added a rubric for this examination yet."), 400
        data = request.get_json()
        scores = data.get("scores") or {}
        rubric_scores = {}
        total = 0
        for rubric in rubrics:
            try:
                score = float(scores.get(str(rubric["id"])))
            except (TypeError, ValueError):
                return jsonify(error=f"Please give marks for {rubric['criterion_name']}."), 400
            if score < 0 or score > rubric["maximum_marks"]:
                return jsonify(error=f"Marks for {rubric['criterion_name']} must be between 0 and {rubric['maximum_marks']:g}."), 400
            rubric_scores[str(rubric["id"])] = score
            total += score * rubric["weightage"]  ## total = sum of (marks x weightage)

        evaluation = booking.evaluation
        if evaluation is None:
            evaluation = Evaluation(booking_id=booking.id, examiner_id=current_user.examiner.id)
            db.session.add(evaluation)
        evaluation.examiner_id = current_user.examiner.id
        evaluation.rubric_scores = rubric_scores
        evaluation.total_marks = round(total, 2)
        evaluation.remarks = (data.get("remarks") or "").strip()
        evaluation.evaluation_date = datetime.now()
        evaluation.status = "submitted"
        booking.status = "completed"
        db.session.commit()
        cache_clear()
        return jsonify(message=f"Evaluation submitted. Total marks: {evaluation.total_marks:g}")
