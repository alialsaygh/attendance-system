import os
import pickle
import time
import cv2
import numpy as np
import face_recognition
from picamera2 import Picamera2
from libcamera import controls

BASE_DIR = os.path.dirname(os.path.abspath(__file__))      # pi_reader
PROJECT_DIR = os.path.dirname(BASE_DIR)                    # attendance-system
ENCODINGS_FILE = os.path.join(PROJECT_DIR, "ml_face", "encodings.pkl")


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

    picam2 = Picamera2()

    config = picam2.create_preview_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )
    picam2.configure(config)

    try:
        picam2.start()

        # Enable autofocus if the camera supports it
        try:
            picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        except Exception:
            pass

        # Let exposure / focus settle
        time.sleep(1.5)

        frame = picam2.capture_array()
        cv2.imwrite("debug_capture.jpg", frame)

    except Exception as e:
        return {
            "verification_status": "not_checked",
            "message": "Camera could not capture image: " + str(e)
        }
    finally:
        try:
            picam2.stop()
        except Exception:
            pass

    # Picamera2 RGB888 is suitable for OpenCV-style BGR arrays,
    # so convert to real RGB for face_recognition
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
        "message": f"Face mismatch. Distance: {distance:.4f}"
    }