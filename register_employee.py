import cv2
import mysql.connector
import pickle
from datetime import datetime
from deepface import DeepFace
from config import DB_CONFIG
import os

def capture_image(emp_code):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera not available")
        return None

    print("Press SPACE to capture, ESC to cancel")

    img_path = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Register Employee", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            print("Cancelled.")
            break
        elif key == 32:
            os.makedirs("employee_photos", exist_ok=True)
            filename = os.path.join(
                "employee_photos",
                f"{emp_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            cv2.imwrite(filename, frame)
            img_path = filename
            print("Image saved:", img_path)
            break

    cap.release()
    cv2.destroyAllWindows()
    return img_path

def compute_embedding(img_path):
    reps = DeepFace.represent(
        img_path=img_path,
        model_name="Facenet512",
        enforce_detection=True,
        detector_backend="opencv"
    )
    
    if len(reps) > 1:
        print(f"Warning: {len(reps)} faces detected. Using the most prominent one.")
    
    emb = reps[0]["embedding"]
    return emb

def insert_employee(emp_code, name, email, phone, post, dept, img_path, embedding):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    enc_bytes = pickle.dumps(embedding)

    sql = """
        INSERT INTO employees
        (employee_code, name, email, phone, post, department, face_encoding, photo_path)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cur.execute(sql, (emp_code, name, email, phone, post, dept, enc_bytes, img_path))
    conn.commit()
    cur.close()
    conn.close()
    print("Employee inserted:", name)

if __name__ == "__main__":
    emp_code = input("Employee code (e.g. EMP001): ")
    name = input("Full Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    post = input("Post (role): ")
    dept = input("Department: ")

    img_path = capture_image(emp_code)
    if img_path:
        try:
            emb = compute_embedding(img_path)
            insert_employee(emp_code, name, email, phone, post, dept, img_path, emb)
        except Exception as e:
            print("Error during embedding/insert:", e)