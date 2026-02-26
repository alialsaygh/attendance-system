from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Session, Module

sessions_bp = Blueprint("sessions_bp", __name__)

def _parse_iso_datetime(value: str):
    # Accepts "2026-02-25T10:00:00"
    return datetime.fromisoformat(value)

@sessions_bp.post("/sessions")
def create_session():
    data = request.get_json(silent=True) or {}
    required = ["module_id", "start_time"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"error": "missing_fields", "message": f"Missing: {', '.join(missing)}"}), 400

    try:
        module_id = int(data["module_id"])
    except (ValueError, TypeError):
        return jsonify({"error": "invalid_fields", "message": "module_id must be an integer"}), 400

    module = Module.query.get(module_id)
    if not module:
        return jsonify({"error": "module_not_found", "message": "Module not found"}), 404

    try:
        start_time = _parse_iso_datetime(str(data["start_time"]))
    except Exception:
        return jsonify({"error": "invalid_fields", "message": "start_time must be ISO format e.g. 2026-02-25T10:00:00"}), 400

    location = (data.get("location") or "").strip() or None

    s = Session(module_id=module_id, start_time=start_time, status="scheduled", location=location)
    db.session.add(s)
    db.session.commit()

    return jsonify({"session_id": s.session_id, "status": s.status, "module_id": s.module_id}), 201


@sessions_bp.post("/sessions/<int:session_id>/start")
def start_session(session_id: int):
    s = Session.query.get(session_id)
    if not s:
        return jsonify({"error": "not_found", "message": "Session not found"}), 404

    # Sprint 1: only 1 active session at a time
    active = Session.query.filter_by(status="active").first()
    if active and active.session_id != session_id:
        return jsonify({"error": "active_session_exists", "message": "Another session is already active"}), 409

    s.status = "active"
    db.session.commit()
    return jsonify({"session_id": s.session_id, "status": s.status}), 200


@sessions_bp.get("/sessions/active")
def get_active_session():
    active = Session.query.filter_by(status="active").first()
    if not active:
        return jsonify({"session_id": None}), 200

    module = Module.query.get(active.module_id)
    return jsonify({
        "session_id": active.session_id,
        "module_id": active.module_id,
        "module_code": module.module_code if module else None,
        "start_time": active.start_time.isoformat(),
        "status": active.status
    }), 200


@sessions_bp.post("/sessions/<int:session_id>/close")
def close_session(session_id: int):
    s = Session.query.get(session_id)
    if not s:
        return jsonify({"error": "not_found", "message": "Session not found"}), 404

    if s.status != "active":
        return jsonify({"error": "not_active", "message": "Session is not active"}), 409

    s.status = "closed"
    db.session.commit()
    return jsonify({"session_id": s.session_id, "status": s.status}), 200