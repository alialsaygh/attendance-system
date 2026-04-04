import time
import requests
from mfrc522 import SimpleMFRC522


FLASK_API = "http://10.32.5.208:5000/api" 
DEVICE_ID = "pi-rfid-reader-01"


reader = SimpleMFRC522()

print("=" * 40)
print("Smart Attendance RFID Reader")
print(f"Connecting to: {FLASK_API}")
print("Waiting for card scan...")
print("=" * 40)

while True:
    try:
        # Wait for a card — this line blocks until a card is detected
        card_id, text = reader.read()

        # Convert to string — this is the card UID
        card_uid = str(card_id)
        print(f"\nCard detected: {card_uid}")

        # Send the UID to your Flask API
        response = requests.post(
            f"{FLASK_API}/attendance/scan",
            json={
                "card_uid":  card_uid,
                "device_id": DEVICE_ID,
            },
            timeout=5
        )

        result = response.json()
        status = result.get("result", "unknown")

        # Show the result clearly
        if status == "accepted":
            print(f"✓ ACCEPTED — {result.get('student_name', '')}")
        elif status == "duplicate":
            print(f"⚠ DUPLICATE — already marked present")
        else:
            print(f"✗ REJECTED — {result.get('message', '')}")

        # Wait 2 seconds before reading again
        # This prevents the same card being scanned twice accidentally
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