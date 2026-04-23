from flask import Blueprint, request, jsonify
from models import db, Card, Student

cards_bp = Blueprint("cards_bp", __name__)

@cards_bp.post("/cards/assign")
def assign_card():
    data = request.get_json(silent=True) or {}
    required = ["student_id", "card_uid"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"error": "missing_fields", "message": f"Missing: {', '.join(missing)}"}), 400

    try:
        student_id = int(data["student_id"])
    except (ValueError, TypeError):
        return jsonify({"error": "invalid_fields", "message": "student_id must be an integer"}), 400

    card_uid = str(data["card_uid"]).strip()
    if not card_uid:
        return jsonify({"error": "invalid_fields", "message": "card_uid cannot be empty"}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "student_not_found", "message": "Student not found"}), 404

    # Sprint 1 strict 1:1
    if Card.query.filter_by(student_id=student_id).first():
        return jsonify({"error": "student_has_card", "message": "Student already has a card"}), 409

    if Card.query.filter_by(card_uid=card_uid).first():
        return jsonify({"error": "card_uid_exists", "message": "Card UID already assigned"}), 409

    c = Card(card_uid=card_uid, student_id=student_id)
    db.session.add(c)
    db.session.commit()

    return jsonify({"message": "Card assigned", "student_id": student_id, "card_uid": card_uid}), 200

@cards_bp.get("/cards/<card_uid>/student")
def get_student_by_card(card_uid):
    card_uid = (card_uid or "").strip()

    if not card_uid:
        return jsonify({"error": "invalid_fields", "message": "card_uid cannot be empty"}), 400

    card = Card.query.filter_by(card_uid=card_uid).first()
    if not card:
        return jsonify({"error": "card_not_found", "message": "Card UID not recognised"}), 404

    student = Student.query.get(card.student_id)
    if not student:
        return jsonify({"error": "student_not_found", "message": "Card not linked to a valid student"}), 404

    return jsonify({
        "student_id": student.student_id,
        "student_number": student.student_number,
        "student_name": f"{student.first_name} {student.last_name}",
    }), 200