from flask import Blueprint, request, jsonify
from models import db, Student

students_bp = Blueprint("students_bp", __name__)

@students_bp.post("/students")
def create_student():
    data = request.get_json(silent=True) or {}

    required = ["student_number", "first_name", "last_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "error": "missing_fields",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    student_number = data["student_number"].strip()
    first_name = data["first_name"].strip()
    last_name = data["last_name"].strip()
    email = (data.get("email") or "").strip() or None

    # Uniqueness checks
    if Student.query.filter_by(student_number=student_number).first():
        return jsonify({
            "error": "student_number_exists",
            "message": "student_number already exists"
        }), 409

    if email and Student.query.filter_by(email=email).first():
        return jsonify({
            "error": "email_exists",
            "message": "email already exists"
        }), 409

    s = Student(
        student_number=student_number,
        first_name=first_name,
        last_name=last_name,
        email=email,
        status="active"
    )

    db.session.add(s)
    db.session.commit()

    return jsonify({"student_id": s.student_id, "message": "Student created"}), 201


@students_bp.get("/students")
def list_students():
    students = Student.query.order_by(Student.student_id.asc()).all()
    return jsonify({
        "students": [
            {
                "student_id": s.student_id,
                "student_number": s.student_number,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "email": s.email,
                "status": s.status
            }
            for s in students
        ]
    }), 200


@students_bp.get("/students/<int:student_id>")
def get_student(student_id: int):
    s = Student.query.get(student_id)
    if not s:
        return jsonify({"error": "not_found", "message": "Student not found"}), 404

    return jsonify({
        "student_id": s.student_id,
        "student_number": s.student_number,
        "first_name": s.first_name,
        "last_name": s.last_name,
        "email": s.email,
        "status": s.status
    }), 200