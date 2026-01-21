import mysql.connector
from datetime import datetime, time
from config import DB_CONFIG

def mark_attendance(emp_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    today = datetime.now().date()
    now = datetime.now()

    cur.execute(
        "SELECT attendance_id, check_in, check_out FROM attendance WHERE emp_id=%s AND date=%s",
        (emp_id, today)
    )
    row = cur.fetchone()

    if row is None:
        office_start = time(9, 0)
        status = "late" if now.time() > office_start else "present"
        cur.execute(
            "INSERT INTO attendance(emp_id, date, check_in, status) VALUES(%s,%s,%s,%s)",
            (emp_id, today, now, status)
        )
        conn.commit()
        result = ("check-in", status, now.strftime("%I:%M %p"))
    elif row[2] is None:
        check_in = row[1]
        total_hours = (now - check_in).total_seconds() / 3600
        cur.execute(
            "UPDATE attendance SET check_out=%s, total_hours=%s WHERE attendance_id=%s",
            (now, total_hours, row[0])
        )
        conn.commit()
        result = ("check-out", f"{total_hours:.2f}", now.strftime("%I:%M %p"))
    else:
        result = ("already-marked", None, None)

    cur.close()
    conn.close()
    return result
