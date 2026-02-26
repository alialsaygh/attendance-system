from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Session, Module, Card, Enrolment, AttendanceRecord, Student

attendance_bp = Blueprint("attendance_bp", __name__)

@attendance_bp.post("/attendance/scan")
def scan_attendance():
    data = request.get_json(silent=True) or {}
    card_uid = (data.get("card_uid") or "").strip()
    device_id = (data.get("device_id") or "").strip() or None

    if not card_uid:
        return jsonify({"error": "missing_fields", "message": "Missing card_uid"}), 400

    # 1) Active session?
    active = Session.query.filter_by(status="active").first()
    if not active:
        return jsonify({"result": "rejected_no_active_session", "message": "No active session"}), 200

    # 2) Known card?
    card = Card.query.filter_by(card_uid=card_uid).first()
    if not card:
        return jsonify({"result": "rejected_unknown_card", "message": "Card UID not recognised"}), 200

    student = Student.query.get(card.student_id)
    if not student:
        return jsonify({"result": "rejected_unknown_card", "message": "Card not linked to a valid student"}), 200

    # 3) Enrolment check
    enrolled = Enrolment.query.filter_by(student_id=student.student_id, module_id=active.module_id).first()
    if not enrolled:
        return jsonify({"result": "rejected_not_enrolled", "message": "Student not enrolled in this module"}), 200

    # 4) Duplicate check (unique session_id + student_id)
    existing = AttendanceRecord.query.filter_by(session_id=active.session_id, student_id=student.student_id).first()
    if existing and existing.result == "accepted":
        return jsonify({"result": "duplicate", "message": "Already marked present"}), 200

    # 5) Accepted
    record = AttendanceRecord(
        session_id=active.session_id,
        student_id=student.student_id,
        tap_time=datetime.utcnow(),
        device_id=device_id,
        result="accepted"
    )

    db.session.add(record)
    db.session.commit()

    return jsonify({
        "result": "accepted",
        "session_id": active.session_id,
        "module_id": active.module_id,
        "student_id": student.student_id,
        "student_name": f"{student.first_name} {student.last_name}",
        "tap_time": record.tap_time.isoformat()
    }), 200


@attendance_bp.get("/sessions/<int:session_id>/attendance")
def get_session_attendance(session_id: int):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "not_found", "message": "Session not found"}), 404

    module = Module.query.get(session.module_id)
    records = AttendanceRecord.query.filter_by(session_id=session_id).order_by(AttendanceRecord.tap_time.asc()).all()

    present = []
    for r in records:
        if r.result != "accepted":
            continue
        s = Student.query.get(r.student_id)
        present.append({
            "student_id": s.student_id,
            "student_number": s.student_number,
            "name": f"{s.first_name} {s.last_name}",
            "tap_time": r.tap_time.isoformat()
        })

    return jsonify({
        "session_id": session_id,
        "module_code": module.module_code if module else None,
        "present": present
    }), 200


@attendance_bp.get("/attendance/active")
def get_active_attendance():
    active = Session.query.filter_by(status="active").first()
    if not active:
        return jsonify({"session_id": None, "present": []}), 200
    # reuse above logic by calling the same query
    module = Module.query.get(active.module_id)
    records = AttendanceRecord.query.filter_by(session_id=active.session_id).order_by(AttendanceRecord.tap_time.asc()).all()

    present = []
    for r in records:
        if r.result != "accepted":
            continue
        s = Student.query.get(r.student_id)
        present.append({
            "student_id": s.student_id,
            "student_number": s.student_number,
            "name": f"{s.first_name} {s.last_name}",
            "tap_time": r.tap_time.isoformat()
        })

    return jsonify({
        "session_id": active.session_id,
        "module_code": module.module_code if module else None,
        "present": present
    }), 200