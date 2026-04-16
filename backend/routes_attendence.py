from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Session, Module, Card, Enrolment, AttendanceRecord, Student

attendance_bp = Blueprint("attendance_bp", __name__)

LATE_THRESHOLD_MINUTES = 15

def calculate_attendance_percentage(student_id, module_id):
    total_sessions = Session.query.filter_by(module_id=module_id).count()

    if total_sessions == 0:
        return 0.0

    attended_sessions = (
        db.session.query(AttendanceRecord.session_id)
        .join(Session, Session.session_id == AttendanceRecord.session_id)
        .filter(
            AttendanceRecord.student_id == student_id,
            Session.module_id == module_id,
            AttendanceRecord.result.in_(["present", "late"])
        )
        .distinct()
        .count()
    )

    return round((attended_sessions / total_sessions) * 100, 2)

@attendance_bp.post("/attendance/scan")
def scan_attendance():
    data      = request.get_json(silent=True) or {}
    card_uid  = (data.get("card_uid") or "").strip()
    device_id = (data.get("device_id") or "").strip() or None

    if not card_uid:
        return jsonify({"error": "missing_fields", "message": "Missing card_uid"}), 400

    active = Session.query.filter_by(status="active").first()
    if not active:
        return jsonify({"result": "rejected_no_active_session",
                        "message": "No active session"}), 200

    card = Card.query.filter_by(card_uid=card_uid).first()
    if not card:
        return jsonify({"result": "rejected_unknown_card",
                        "message": "Card UID not recognised"}), 200

    student = Student.query.get(card.student_id)
    if not student:
        return jsonify({"result": "rejected_unknown_card",
                        "message": "Card not linked to a valid student"}), 200

    enrolled = Enrolment.query.filter_by(
        student_id=student.student_id,
        module_id=active.module_id
    ).first()
    if not enrolled:
        return jsonify({"result": "rejected_not_enrolled",
                        "message": "Student not enrolled in this module"}), 200

    existing = AttendanceRecord.query.filter_by(
        session_id=active.session_id,
        student_id=student.student_id
    ).first()
    if existing:
        return jsonify({
            "result":       "duplicate",
            "message":      "Already marked present",
            "student_name": f"{student.first_name} {student.last_name}",
        }), 200

    now = datetime.utcnow()
    minutes_since_start = (now - active.start_time).total_seconds() / 60
    result = "present" if minutes_since_start <= LATE_THRESHOLD_MINUTES else "late"

    record = AttendanceRecord(
        session_id=active.session_id,
        student_id=student.student_id,
        tap_time=now,
        device_id=device_id,
        result=result
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "result":       result,
        "session_id":   active.session_id,
        "module_id":    active.module_id,
        "student_id":   student.student_id,
        "student_name": f"{student.first_name} {student.last_name}",
        "tap_time":     record.tap_time.isoformat(),
        "minutes_since_start": round(minutes_since_start, 1),
    }), 200


@attendance_bp.get("/sessions/<int:session_id>/attendance")
def get_session_attendance(session_id: int):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "not_found", "message": "Session not found"}), 404

    module  = Module.query.get(session.module_id)
    records = AttendanceRecord.query.filter_by(
        session_id=session_id
    ).order_by(AttendanceRecord.tap_time.asc()).all()

    all_records = []
    for r in records:
        s = Student.query.get(r.student_id)
        if s:
            all_records.append({
                "student_id":     s.student_id,
                "student_number": s.student_number,
                "name":           f"{s.first_name} {s.last_name}",
                "tap_time":       r.tap_time.isoformat(),
                "result":         r.result,
            })

    present = [r for r in all_records if r["result"] == "present"]
    late    = [r for r in all_records if r["result"] == "late"]
    absent  = [r for r in all_records if r["result"] == "absent"]

    return jsonify({
        "session_id":  session_id,
        "module_code": module.module_code if module else None,
        "records":     all_records,
        "present":     present,
        "summary": {
            "present": len(present),
            "late":    len(late),
            "absent":  len(absent),
        }
    }), 200


@attendance_bp.get("/attendance/active")
def get_active_attendance():
    active = Session.query.filter_by(status="active").first()
    if not active:
        return jsonify({"session_id": None, "present": [], "late": []}), 200

    module  = Module.query.get(active.module_id)
    records = AttendanceRecord.query.filter_by(
        session_id=active.session_id
    ).order_by(AttendanceRecord.tap_time.asc()).all()

    present = []
    late    = []

    for r in records:
        s = Student.query.get(r.student_id)
        if not s:
            continue
        entry = {
            "student_id":     s.student_id,
            "student_number": s.student_number,
            "name":           f"{s.first_name} {s.last_name}",
            "tap_time":       r.tap_time.isoformat(),
            "result":         r.result,
        }
        if r.result == "present":
            present.append(entry)
        elif r.result == "late":
            late.append(entry)

    return jsonify({
        "session_id":  active.session_id,
        "module_code": module.module_code if module else None,
        "present":     present,
        "late":        late,
        "total":       len(present) + len(late),
    }), 200


@attendance_bp.get("/attendance/<int:student_id>/<int:module_id>/percentage")
def get_attendance_percentage(student_id, module_id):
    percentage = calculate_attendance_percentage(student_id, module_id)

    return jsonify({
        "student_id": student_id,
        "module_id": module_id,
        "attendance_percentage": percentage
    }), 200