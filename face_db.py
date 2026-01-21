import mysql.connector
import pickle
import numpy as np
from config import DB_CONFIG

def load_employee_embeddings():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT emp_id, name, post, face_encoding FROM employees WHERE status='active'")
        
        employees = []
        rows = cur.fetchall()
        
        for emp_id, name, post, enc in rows:
            if enc is None:
                continue
            
            try:
                emb = pickle.loads(enc)
                
                if emb is not None and len(emb) > 0:
                    employees.append({
                        "emp_id": emp_id,
                        "name": name,
                        "post": post,
                        "embedding": np.array(emb, dtype="float32")
                    })
            except (pickle.UnpicklingError, EOFError, IndexError) as e:
                print(f"Warning: Skipping corrupt embedding for EmpID {emp_id}. Error: {e}")
                continue

        cur.close()
        conn.close()
        
        print(f"Successfully loaded {len(employees)} active profiles.")
        return employees

    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return []