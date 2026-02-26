from flask import Blueprint, request, jsonify
from models import db, Module

modules_bp = Blueprint("modules_bp", __name__)

@modules_bp.post("/modules")
def create_module():
    data = request.get_json(silent=True) or {}

    required = ["module_code", "module_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "error": "missing_fields",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    module_code = data["module_code"].strip()
    module_name = data["module_name"].strip()

    # Uniqueness checks
    if Module.query.filter_by(module_code=module_code).first():
        return jsonify({
            "error": "module_code_exists",
            "message": "module_code already exists"
        }), 409

    m = Module(
        module_code=module_code,
        module_name=module_name
    )

    db.session.add(m)
    db.session.commit()

    return jsonify({"module_id": m.module_id, "message": "Module created"}), 201


@modules_bp.get("/modules")
def list_modules():
    modules = Module.query.order_by(Module.module_id.asc()).all()
    return jsonify({
        "modules": [
            {
                "module_id": m.module_id,
                "module_code": m.module_code,
                "module_name": m.module_name
            }
            for m in modules
        ]
    }), 200


@modules_bp.get("/modules/<int:module_id>")
def get_module(module_id: int):
    m = Module.query.get(module_id)
    if not m:
        return jsonify({"error": "not_found", "message": "Module not found"}), 404

    return jsonify({
        "module_id": m.module_id,
        "module_code": m.module_code,
        "module_name": m.module_name
    }), 200
