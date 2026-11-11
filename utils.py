from datetime import datetime, date, time
from model import Booking, Slot

EXAM_TYPES = ["viva", "practical", "project_demo", "assessment"]
EXAM_STATUSES = ["draft", "slot_creation", "booking_open", "closed", "completed"]


def missing_fields(data, fields):
    ## returns the name of the first empty field (None if everything is filled)
    for field in fields:
        if data.get(field) is None or str(data.get(field)).strip() == "":
            return field.replace("_", " ")
    return None


def matches(query, *values):
    ## used by all the search functions, true if query is inside any of the values
    query = query.lower().strip()
    return any(query in str(value).lower() for value in values if value is not None)


def slot_creation_is_open(exam):
    ## admin opens it with the status, and it only works inside the slot creation dates
    now = datetime.now()
    return exam.status == "slot_creation" and exam.slot_creation_start <= now <= exam.slot_creation_end


def booking_is_open(exam):
    now = datetime.now()
    return exam.status == "booking_open" and exam.slot_booking_start <= now <= exam.slot_booking_end


def slots_can_be_changed(exam):
    ## examiners can update / remove slots only before student booking begins
    return exam.status in ("draft", "slot_creation") and datetime.now() < exam.slot_booking_start


def refresh_slot(slot):
    ## recount the seats from the bookings, and mark the slot full when no seats are left
    taken = Booking.query.filter(Booking.slot_id == slot.id, Booking.status != "cancelled").count()
    slot.available_seats = slot.max_student_capacity - taken
    if slot.status in ("available", "full"):
        slot.status = "full" if slot.available_seats <= 0 else "available"


def read_slot(data):
    ## reads the slot form (used by examiner create/edit and admin reschedule)
    missing = missing_fields(data, ["date", "start_time", "end_time", "max_student_capacity"])
    if missing:
        return None, f"Please fill the {missing}."
    try:
        values = {
            "date": date.fromisoformat(data["date"]),
            "start_time": time.fromisoformat(data["start_time"]),
            "end_time": time.fromisoformat(data["end_time"]),
            "max_student_capacity": int(data["max_student_capacity"]),
            "meeting_link": (data.get("meeting_link") or "").strip()
        }
    except ValueError:
        return None, "Please check the date, time and capacity."
    if values["start_time"] >= values["end_time"]:
        return None, "End time must be after start time."
    if values["max_student_capacity"] <= 0:
        return None, "Capacity must be at least 1."
    return values, None


def slot_overlaps(examiner_id, slot_date, start_time, end_time, slot_id=None):
    ## an examiner can not be in two slots at the same time
    slots = Slot.query.filter(Slot.examiner_id == examiner_id, Slot.date == slot_date, Slot.status != "cancelled").all()
    for slot in slots:
        if slot.id != slot_id and start_time < slot.end_time and slot.start_time < end_time:
            return True
    return False
