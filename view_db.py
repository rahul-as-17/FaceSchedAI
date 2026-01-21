import mysql.connector
from config import DB_CONFIG

def view_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("\n--- EMPLOYEE TABLE ---")
        cur.execute("SELECT emp_id, name, post FROM employees")
        for row in cur.fetchall():
            print(row)

        print("\n--- ATTENDANCE TABLE (Today) ---")
        cur.execute("SELECT * FROM attendance WHERE date = CURDATE()")
        rows = cur.fetchall()
        
        if not rows:
            print("No attendance records found for today.")
        else:
            for row in rows:
                print(row)

        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    view_data()