from flask import Blueprint, request, jsonify
from models import db, Enrolment, Student, Module

enrolments_bp = Blueprint("enrolments_bp", __name__)

@enrolments_bp.post("/enrolments")
def create_enrolment():
    data = request.get_json(silent=True) or {}

    # Only require these two in Sprint 1
    required = ["student_id", "module_id"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({
            "error": "missing_fields",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    # Convert to int safely
    try:
        student_id = int(data["student_id"])
        module_id = int(data["module_id"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "invalid_fields",
            "message": "student_id and module_id must be integers"
        }), 400

    # Check student exists
    if not Student.query.get(student_id):
        return jsonify({"error": "student_not_found", "message": "Student not found"}), 404

    # Check module exists
    if not Module.query.get(module_id):
        return jsonify({"error": "module_not_found", "message": "Module not found"}), 404

    # Check already enrolled (unique student+module)
    if Enrolment.query.filter_by(student_id=student_id, module_id=module_id).first():
        return jsonify({"error": "already_enrolled", "message": "Student already enrolled"}), 409

    e = Enrolment(student_id=student_id, module_id=module_id)
    db.session.add(e)
    db.session.commit()

    return jsonify({
        "message": "Student enrolled",
        "enrolment_id": e.enrolment_id,
        "student_id": e.student_id,
        "module_id": e.module_id,
        "enrolled_at": e.enrolled_at.isoformat()
    }), 201


@enrolments_bp.get("/enrolments")
def list_enrolments():
    enrolments = Enrolment.query.order_by(Enrolment.enrolment_id.asc()).all()
    return jsonify({
        "enrolments": [
            {
                "enrolment_id": e.enrolment_id,
                "student_id": e.student_id,
                "module_id": e.module_id,
                "enrolled_at": e.enrolled_at.isoformat()
            }
            for e in enrolments
        ]
    }), 200


@enrolments_bp.get("/enrolments/<int:enrolment_id>")
def get_enrolment(enrolment_id: int):
    e = Enrolment.query.get(enrolment_id)
    if not e:
        return jsonify({"error": "not_found", "message": "Enrolment not found"}), 404

    return jsonify({
        "enrolment_id": e.enrolment_id,
        "student_id": e.student_id,
        "module_id": e.module_id,
        "enrolled_at": e.enrolled_at.isoformat()
    }), 200