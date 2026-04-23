import time
import requests
from mfrc522 import SimpleMFRC522
from ml_face.verify_face import verify_student_face

FLASK_API = "http://10.32.20.224:5000/api"
DEVICE_ID = "pi-rfid-reader-01"

reader = SimpleMFRC522()

print("=" * 40)
print("Smart Attendance RFID Reader")
print(f"Connecting to: {FLASK_API}")
print("Waiting for card scan...")
print("=" * 40)

while True:
    try:
        card_id, text = reader.read()
        card_uid = str(card_id)
        print(f"\nCard detected: {card_uid}")

        # Step 1: ask Flask which student belongs to this card
        lookup_response = requests.get(
            f"{FLASK_API}/cards/{card_uid}/student",
            timeout=5
        )

        if lookup_response.status_code != 200:
            lookup_result = lookup_response.json()
            print(f"✗ REJECTED — {lookup_result.get('message', 'Card lookup failed')}")
            time.sleep(2)
            continue

        student_data = lookup_response.json()
        student_number = student_data.get("student_number")
        student_name = student_data.get("student_name", "")

        print(f"Student linked to card: {student_name} ({student_number})")

        # Step 2: verify face locally on the Pi
        verification = verify_student_face(student_number)
        verification_status = verification.get("verification_status", "not_checked")
        verification_message = verification.get("message", "")

        print(f"Face check: {verification_status} — {verification_message}")

        # Step 3: send final attendance scan to Flask
        response = requests.post(
            f"{FLASK_API}/attendance/scan",
            json={
                "card_uid": card_uid,
                "device_id": DEVICE_ID,
                "verification_status": verification_status,
            },
            timeout=5
        )

        result = response.json()
        status = result.get("result", "unknown")
        returned_verification = result.get("verification_status", verification_status)

        if status in ["present", "late"]:
            if returned_verification == "verified":
                print(f"✓ ACCEPTED — {result.get('student_name', '')} ({status}) [VERIFIED]")
            elif returned_verification == "mismatch":
                print(f"⚠ ACCEPTED — {result.get('student_name', '')} ({status}) [MISMATCH]")
            elif returned_verification == "skipped_no_encoding":
                print(f"✓ ACCEPTED — {result.get('student_name', '')} ({status}) [NO PHOTO]")
            else:
                print(f"✓ ACCEPTED — {result.get('student_name', '')} ({status})")
        elif status == "duplicate":
            print("⚠ DUPLICATE — already marked present")
        else:
            print(f"✗ REJECTED — {result.get('message', '')}")

        time.sleep(2)

    except KeyboardInterrupt:
        print("\nReader stopped by user.")
        break
    except requests.exceptions.ConnectionError:
        print("Cannot reach Flask API — is it running?")
        time.sleep(3)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)