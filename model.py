from flask_sqlalchemy import SQLAlchemy as SA
from flask_login import UserMixin


db = SA()

examiner_examination = db.Table(
    'examiner_examination',
    db.Column('examiner_id', db.Integer, db.ForeignKey('examiner.id'), primary_key=True),
    db.Column('examination_id', db.Integer, db.ForeignKey('examination.id'), primary_key=True)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  ## admin, student, examiner
    fname = db.Column(db.String(80), nullable=False)
    lname = db.Column(db.String(80), nullable=False)
    pwd_hash = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(40), nullable=False)
    admin_approval_status = db.Column(db.String(20), default="pending", nullable=False)
    admin_enforced_blacklist_status = db.Column(db.Boolean, default=False, nullable=False)

    admin = db.relationship('Admin', back_populates='user', uselist=False)
    student = db.relationship('Student', back_populates='user', uselist=False)
    examiner = db.relationship('Examiner', back_populates='user', uselist=False)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aid = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)
    user = db.relationship('User', back_populates='admin')


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    major = db.Column(db.String(20), nullable=False)
    university = db.Column(db.String(80), nullable=False)
    gpa = db.Column(db.String(20), nullable=False)

    user = db.relationship('User', back_populates='student')
    bookings = db.relationship('Booking', back_populates='student')


class Examiner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    contact_details = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)

    user = db.relationship('User', back_populates='examiner')
    examinations = db.relationship('Examination', secondary=examiner_examination, back_populates='examiners')
    slots = db.relationship('Slot', back_populates='examiner')
    evaluations = db.relationship('Evaluation', back_populates='examiner')


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(30), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)

    examinations = db.relationship('Examination', back_populates='course')


class Examination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    examination_name = db.Column(db.String(100), nullable=False)
    examination_type = db.Column(db.String(30), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  ## minutes
    maximum_marks = db.Column(db.Float, nullable=False)
    slot_creation_start = db.Column(db.DateTime, nullable=False)
    slot_creation_end = db.Column(db.DateTime, nullable=False)
    slot_booking_start = db.Column(db.DateTime, nullable=False)
    slot_booking_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="draft", nullable=False)
    results_published = db.Column(db.Boolean, default=False, nullable=False)
    instructions = db.Column(db.String(500), nullable=True)

    course = db.relationship('Course', back_populates='examinations')
    examiners = db.relationship('Examiner', secondary=examiner_examination, back_populates='examinations')
    rubrics = db.relationship('Rubric', back_populates='examination')
    slots = db.relationship('Slot', back_populates='examination')
    bookings = db.relationship('Booking', back_populates='examination')


class Rubric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    criterion_name = db.Column(db.String(100), nullable=False)
    maximum_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=True)

    examination = db.relationship('Examination', back_populates='rubrics')


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_student_capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="available", nullable=False)
    meeting_link = db.Column(db.String(200), nullable=True)

    examination = db.relationship('Examination', back_populates='slots')
    examiner = db.relationship('Examiner', back_populates='slots')
    bookings = db.relationship('Booking', back_populates='slot')


class Booking(db.Model):
    __table_args__ = (db.UniqueConstraint('student_id', 'examination_id'),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    examination_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slot.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="booked", nullable=False)

    student = db.relationship('Student', back_populates='bookings')
    examination = db.relationship('Examination', back_populates='bookings')
    slot = db.relationship('Slot', back_populates='bookings')
    evaluation = db.relationship('Evaluation', back_populates='booking', uselist=False)


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), unique=True, nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner.id'), nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    rubric_scores = db.Column(db.JSON, nullable=True)
    remarks = db.Column(db.String(500), nullable=True)
    evaluation_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="submitted", nullable=False)

    booking = db.relationship('Booking', back_populates='evaluation')
    examiner = db.relationship('Examiner', back_populates='evaluations')
