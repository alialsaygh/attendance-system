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

# get attendance summary for a student - percentage per module + overall
# this is used by the student dashboard and tutor module page
@students_bp.get("/students/<int:student_id>/attendance-summary")
def get_attendance_summary(student_id):
    from models import Session, AttendanceRecord, Enrolment, Module

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "not_found", "message": "Student not found"}), 404

    # get all modules this student is enrolled in
    enrolments = Enrolment.query.filter_by(student_id=student_id).all()

    module_summaries = []
    total_sessions_all  = 0
    total_attended_all  = 0

    for e in enrolments:
        module = Module.query.get(e.module_id)
        if not module:
            continue

        # only count closed sessions - active ones are not finished yet
        closed_sessions = Session.query.filter_by(
            module_id=e.module_id,
            status='closed'
        ).all()

        total_sessions = len(closed_sessions)

        if total_sessions == 0:
            # no sessions run yet for this module
            module_summaries.append({
                'module_id':   module.module_id,
                'module_code': module.module_code,
                'module_name': module.module_name,
                'total_sessions':   0,
                'present_count':    0,
                'late_count':       0,
                'absent_count':     0,
                'attended_count':   0,
                'percentage':       None,  # shown as N/A
                'late_percentage':  None,
                'classification':   'No sessions yet',
            })
            continue

        # count this students records across all closed sessions
        present_count = 0
        late_count    = 0
        absent_count  = 0

        for session in closed_sessions:
            record = AttendanceRecord.query.filter_by(
                session_id=session.session_id,
                student_id=student_id
            ).first()

            if record:
                if record.result == 'present':
                    present_count += 1
                elif record.result == 'late':
                    late_count += 1
                else:
                    absent_count += 1
            else:
                # no record means absent
                absent_count += 1

        # sessions attended = present + late
        attended_count = present_count + late_count

        # calculate percentage
        percentage = round((attended_count / total_sessions) * 100, 1)

        # late percentage out of attended sessions only
        if attended_count > 0:
            late_percentage = round((late_count / attended_count) * 100, 1)
        else:
            late_percentage = 0.0

        # classification using rule based thresholds
        # needs at least 3 sessions to classify
        if total_sessions < 3:
            classification = 'Insufficient data'
        elif percentage >= 80 and late_percentage < 20:
            classification = 'On Time'
        elif percentage >= 70 and late_percentage >= 20:
            classification = 'Frequently Late'
        elif percentage >= 50:
            classification = 'Irregular'
        else:
            classification = 'At Risk'

        # add to overall totals
        total_sessions_all += total_sessions
        total_attended_all += attended_count

        module_summaries.append({
            'module_id':        module.module_id,
            'module_code':      module.module_code,
            'module_name':      module.module_name,
            'total_sessions':   total_sessions,
            'present_count':    present_count,
            'late_count':       late_count,
            'absent_count':     absent_count,
            'attended_count':   attended_count,
            'percentage':       percentage,
            'late_percentage':  late_percentage,
            'classification':   classification,
        })

    # calculate overall percentage across all modules
    if total_sessions_all > 0:
        overall_percentage = round((total_attended_all / total_sessions_all) * 100, 1)
    else:
        overall_percentage = None

    return jsonify({
        'student_id':         student_id,
        'student_number':     student.student_number,
        'name':               student.first_name + ' ' + student.last_name,
        'modules':            module_summaries,
        'overall_percentage': overall_percentage,
        'total_sessions_all': total_sessions_all,
        'total_attended_all': total_attended_all,
    }), 200