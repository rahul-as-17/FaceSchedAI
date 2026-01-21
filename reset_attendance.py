import mysql.connector
from config import DB_CONFIG

def reset_todays_attendance():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM attendance WHERE date = CURDATE()")
        conn.commit()
        print("✔ Today's attendance records deleted. You can check in again.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    reset_todays_attendance()