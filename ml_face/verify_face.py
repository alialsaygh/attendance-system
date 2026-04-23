import os
import pickle
import cv2
import numpy as np
import face_recognition

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODINGS_FILE = os.path.join(BASE_DIR, "encodings.pkl")


def load_encodings():
    if not os.path.exists(ENCODINGS_FILE):
        return {}

    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)

    student_numbers = data.get("student_numbers", [])
    encodings = data.get("encodings", [])

    known = {}
    for student_number, encoding in zip(student_numbers, encodings):
        known[str(student_number)] = np.array(encoding)

    return known


def verify_student_face(student_number, tolerance=0.5):
    known = load_encodings()
    student_number = str(student_number)

    if student_number not in known:
        return {
            "verification_status": "skipped_no_encoding",
            "message": "No stored encoding for this student."
        }

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {
            "verification_status": "mismatch",
            "message": "Camera could not be opened."
        }

    try:
        ok, frame = cap.read()
        if not ok:
            return {
                "verification_status": "mismatch",
                "message": "Could not capture image."
            }

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        if len(face_encodings) == 0:
            return {
                "verification_status": "mismatch",
                "message": "No face detected."
            }

        if len(face_encodings) > 1:
            return {
                "verification_status": "mismatch",
                "message": "More than one face detected."
            }

        live_encoding = face_encodings[0]
        saved_encoding = known[student_number]

        distance = face_recognition.face_distance([saved_encoding], live_encoding)[0]

        if distance <= tolerance:
            return {
                "verification_status": "verified",
                "message": "Face verified."
            }

        return {
            "verification_status": "mismatch",
            "message": "Face mismatch."
        }

    finally:
        cap.release()
        cv2.destroyAllWindows()