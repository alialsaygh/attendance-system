from flask import Flask, jsonify
import os
from models import db

def create_app():
    app = Flask(__name__)
    

    # Config
    db_url = os.getenv("DATABASE_URL", "sqlite:///attendance.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    # Blueprints
    from routes_students import students_bp
    from routes_modules import modules_bp
    from routes_enrolments import enrolments_bp
    from routes_card import cards_bp
    from routes_sessions import sessions_bp
    from routes_attendence import attendance_bp

    app.register_blueprint(students_bp, url_prefix="/api")
    app.register_blueprint(modules_bp, url_prefix="/api")
    app.register_blueprint(enrolments_bp, url_prefix="/api")
    app.register_blueprint(cards_bp, url_prefix="/api")
    app.register_blueprint(sessions_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    
    
    with app.app_context():
        db.create_all()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)