import cv2
import numpy as np
from deepface import DeepFace
from face_db import load_employee_embeddings
from attendance import mark_attendance

THRESHOLD = 0.5 

def find_cosine_distance(source_representation, test_representation):
    a = np.matmul(np.transpose(source_representation), test_representation)
    b = np.sum(np.multiply(source_representation, source_representation))
    c = np.sum(np.multiply(test_representation, test_representation))
    return 1 - (a / (np.sqrt(b) * np.sqrt(c)))

def recognize_face(frame, known_emps):
    try:
        reps = DeepFace.represent(
            img_path=frame,
            model_name="Facenet512",
            detector_backend="opencv",
            enforce_detection=False 
        )
    except Exception:
        return None, None

    if not reps:
        return None, None

    target_rep = reps[0]
    target_embedding = np.array(target_rep["embedding"], dtype="float32")
    facial_area = target_rep.get("facial_area", None)

    best_emp = None
    best_dist = 1.0

    for emp in known_emps:
        db_embedding = np.array(emp["embedding"], dtype="float32")
        dist = find_cosine_distance(target_embedding, db_embedding)
        
        if dist < best_dist:
            best_dist = dist
            best_emp = emp

    if best_emp:
        print(f"Match: {best_emp['name']} | Dist: {best_dist:.4f}")

    if best_dist < THRESHOLD:
        return best_emp, facial_area
        
    return None, facial_area

if __name__ == "__main__":
    known_emps = load_employee_embeddings()
    if not known_emps:
        print("No employees in DB. Run register_employee.py first.")
        exit()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    print(f"System Ready. Threshold: {THRESHOLD}")
    print("Press Q to quit")

    last_emp_id = None
    stable_count = 0
    current_emp = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        emp, face_box = recognize_face(frame, known_emps)

        if face_box:
            x, y, w, h = face_box['x'], face_box['y'], face_box['w'], face_box['h']
            color = (0, 0, 255)
            name_tag = "Unknown"

            if emp:
                color = (0, 255, 0)
                name_tag = f"{emp['name']} ({emp['post']})"

                if current_emp and emp["emp_id"] == current_emp["emp_id"]:
                    stable_count += 1
                else:
                    current_emp = emp
                    stable_count = 1

                if stable_count >= 3 and emp["emp_id"] != last_emp_id:
                    print(f"Recognized Stable: {emp['name']}")
                    
                    action, info, time_str = mark_attendance(emp["emp_id"])
                    
                    if action == "check-in":
                        print(f"✔ Check-in: {time_str}, status={info}")
                    elif action == "check-out":
                        print(f"✔ Check-out: {time_str}, hours={info}")
                    else:
                        print("Attendance already done.")
                    
                    last_emp_id = emp["emp_id"]
                    stable_count = 0
            else:
                stable_count = 0
                current_emp = None
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, name_tag, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("FaceSched AI", frame)

        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
            break

    cap.release()
    cv2.destroyAllWindows()