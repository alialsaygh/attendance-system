from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = "students"
    student_id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Card(db.Model):
    __tablename__ = "cards"
    card_id = db.Column(db.Integer, primary_key=True)
    card_uid = db.Column(db.String(100), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), unique=True, nullable=False)

class Module(db.Model):
    __tablename__ = "modules"
    module_id = db.Column(db.Integer, primary_key=True)
    module_code = db.Column(db.String(50), unique=True, nullable=False)
    module_name = db.Column(db.String(200), nullable=False)

class Enrolment(db.Model):
    __tablename__ = "enrolments"
    enrolment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.module_id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("student_id", "module_id", name="uq_student_module"),
    )

class Session(db.Model):
    __tablename__ = "sessions"
    session_id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.module_id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="scheduled", nullable=False)  # scheduled/active/closed
    location = db.Column(db.String(100), nullable=True)

class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"
    attendance_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.session_id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    tap_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    device_id = db.Column(db.String(100), nullable=True)
    result = db.Column(db.String(50), nullable=False)  # accepted/duplicate/rejected...

    __table_args__ = (
        db.UniqueConstraint("session_id", "student_id", name="uq_session_student_once"),
    )