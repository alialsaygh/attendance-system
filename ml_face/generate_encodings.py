import os
import pickle
import face_recognition

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

PHOTOS_DIR = os.path.join(PROJECT_DIR, "web", "media", "student_photos")
OUTPUT_FILE = os.path.join(BASE_DIR, "encodings.pkl")

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")


def generate_encodings():
    # Check folder exists
    if not os.path.exists(PHOTOS_DIR):
        print(f"Photo folder not found: {PHOTOS_DIR}")
        print("Please create the student_photos folder and add student images.")
        return

    # Get all valid image files
    photo_files = [
        f for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith(VALID_EXTENSIONS)
    ]

    # Handle empty folder
    if not photo_files:
        print("No photos found in student_photos folder.")
        print("Nothing to encode.")
        return

    known_encodings = []
    student_numbers = []

    print(f"Found {len(photo_files)} photo(s). Starting encoding process...\n")

    for filename in photo_files:
        image_path = os.path.join(PHOTOS_DIR, filename)
        student_number = os.path.splitext(filename)[0]

        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) == 0:
                print(f"[SKIPPED] {filename} - No detectable face found.")
                continue

            if len(encodings) > 1:
                print(f"[SKIPPED] {filename} - More than one face found.")
                continue

            known_encodings.append(encodings[0])
            student_numbers.append(student_number)

            print(f"[OK] {filename} encoded successfully.")

        except Exception as e:
            print(f"[ERROR] {filename} - {e}")

    # Save results
    data = {
        "student_numbers": student_numbers,
        "encodings": known_encodings
    }

    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(data, f)

    print("\nEncoding process finished.")
    print(f"Valid encodings saved: {len(student_numbers)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_encodings()