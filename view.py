## turns database objects into dicts so flask can send them to vue as json
from datetime import datetime


def fmt_datetime(value):
    return value.strftime("%Y-%m-%dT%H:%M") if value else None  ## same format as <input type="datetime-local">

def fmt_date(value):
    return value.isoformat() if value else None

def fmt_time(value):
    return value.strftime("%H:%M") if value else None

def full_name(user):
    return user.fname + " " + user.lname


def course_view(course):
    return {
        "id": course.id,
        "course_code": course.course_code,
        "course_name": course.course_name,
        "description": course.description,
        "status": course.status,
        "total_examinations": len(course.examinations)
    }


def examination_view(exam):
    return {
        "id": exam.id,
        "course_id": exam.course_id,
        "course_code": exam.course.course_code,
        "course_name": exam.course.course_name,
        "examination_name": exam.examination_name,
        "examination_type": exam.examination_type,
        "duration": exam.duration,
        "maximum_marks": exam.maximum_marks,
        "slot_creation_start": fmt_datetime(exam.slot_creation_start),
        "slot_creation_end": fmt_datetime(exam.slot_creation_end),
        "slot_booking_start": fmt_datetime(exam.slot_booking_start),
        "slot_booking_end": fmt_datetime(exam.slot_booking_end),
        "status": exam.status,
        "results_published": exam.results_published,
        "instructions": exam.instructions or "",
        "examiners": [{"id": e.id, "name": full_name(e.user)} for e in exam.examiners],
        "total_rubrics": len(exam.rubrics),
        "total_slots": len([s for s in exam.slots if s.status != "cancelled"]),
        "total_bookings": len([b for b in exam.bookings if b.status != "cancelled"])
    }


def rubric_view(rubric):
    return {
        "id": rubric.id,
        "examination_id": rubric.examination_id,
        "criterion_name": rubric.criterion_name,
        "maximum_marks": rubric.maximum_marks,
        "weightage": rubric.weightage,
        "description": rubric.description or ""
    }


def slot_view(slot):
    return {
        "id": slot.id,
        "examination_id": slot.examination_id,
        "examination_name": slot.examination.examination_name,
        "course_code": slot.examination.course.course_code,
        "examiner_id": slot.examiner_id,
        "examiner_name": full_name(slot.examiner.user),
        "date": fmt_date(slot.date),
        "start_time": fmt_time(slot.start_time),
        "end_time": fmt_time(slot.end_time),
        "max_student_capacity": slot.max_student_capacity,
        "available_seats": slot.available_seats,
        "booked_students": slot.max_student_capacity - slot.available_seats,
        "status": slot.status,
        "meeting_link": slot.meeting_link or ""
    }


def evaluation_view(evaluation):
    if evaluation is None:
        return None
    return {
        "id": evaluation.id,
        "total_marks": evaluation.total_marks,
        "rubric_scores": evaluation.rubric_scores or {},
        "remarks": evaluation.remarks or "",
        "evaluation_date": fmt_datetime(evaluation.evaluation_date),
        "status": evaluation.status,
        "examiner_name": full_name(evaluation.examiner.user)
    }


def booking_view(booking, for_student=False):
    exam = booking.examination
    slot = booking.slot
    data = {
        "id": booking.id,
        "student_id": booking.student_id,
        "student_name": full_name(booking.student.user),
        "student_email": booking.student.user.email,
        "examination_id": exam.id,
        "examination_name": exam.examination_name,
        "course_code": exam.course.course_code,
        "course_name": exam.course.course_name,
        "instructions": exam.instructions or "",
        "maximum_marks": exam.maximum_marks,
        "results_published": exam.results_published,
        "slot_id": slot.id,
        "date": fmt_date(slot.date),
        "start_time": fmt_time(slot.start_time),
        "end_time": fmt_time(slot.end_time),
        "examiner_name": full_name(slot.examiner.user),
        "meeting_link": slot.meeting_link or "",
        "booking_date": fmt_datetime(booking.booking_date),
        "status": booking.status,
        "evaluation": evaluation_view(booking.evaluation)
    }
    if for_student:
        ## students only see marks after admin publishes the results
        if not exam.results_published:
            data["evaluation"] = None
        data["can_cancel"] = booking.status == "booked" and datetime.now() < exam.slot_booking_end
    return data


def student_view(student):
    user = student.user
    return {
        "id": student.id,
        "user_id": user.id,
        "name": full_name(user),
        "fname": user.fname,
        "lname": user.lname,
        "username": user.username,
        "email": user.email,
        "gender": user.gender,
        "university": student.university,
        "major": student.major,
        "gpa": student.gpa,
        "banned": user.admin_enforced_blacklist_status,
        "total_bookings": len([b for b in student.bookings if b.status != "cancelled"])
    }


def examiner_view(examiner):
    user = examiner.user
    return {
        "id": examiner.id,
        "user_id": user.id,
        "name": full_name(user),
        "fname": user.fname,
        "lname": user.lname,
        "username": user.username,
        "email": user.email,
        "department": examiner.department,
        "contact_details": examiner.contact_details,
        "status": examiner.status,
        "assigned_examinations": len(examiner.examinations),
        "total_slots": len([s for s in examiner.slots if s.status != "cancelled"])
    }
