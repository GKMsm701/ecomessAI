import database as db
from datetime import datetime, timedelta, date

db.initialize_db()
print("[INFO] Seeding complete EcoMESS data (Students, Staff, Institutions, Middleman, Logistics)...")

def get_or_create(username, password, role, name, email, inst_type='general'):
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row["id"]
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, password, role, full_name, email, institution_type)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (username, password, role, name, email, inst_type))
    conn.commit()
    uid = cur.lastrowid
    cur.close()
    conn.close()
    return uid

# 1. Students & Staff
s1_id = get_or_create("student1", "pass123", "student", "Alice Smith", "alice@student.com", "Institution")
s2_id = get_or_create("student2", "pass123", "student", "Bob Jones", "bob@student.com", "Institution")

staff1_id = get_or_create("staff1", "pass123", "staff", "Charlie Brown", "charlie@staff.com", "Institution")
staff2_id = get_or_create("staff2", "pass123", "staff", "Diana Prince", "diana@staff.com", "Institution")

# 2. Add Attendance
db.upsert_attendance(s1_id, date.today(), 'present', '08:00:00', '20:00:00')
db.upsert_attendance(s2_id, date.today(), 'absent', None, None)
db.upsert_attendance(staff1_id, date.today(), 'present', '07:00:00', '18:00:00')

# 3. Add Polls
db.submit_poll(s1_id, date.today() + timedelta(days=1), 'Paneer Butter Masala')
db.submit_poll(s2_id, date.today() + timedelta(days=1), 'Veg Biryani')

# 4. Generate Mess Bills
db.generate_monthly_bill(s1_id, date.today().month, date.today().year)
db.generate_monthly_bill(s2_id, date.today().month, date.today().year)

print("[OK] Base Institution Data (Students, Staff, Attendance, Polls, Bills) populated.")
