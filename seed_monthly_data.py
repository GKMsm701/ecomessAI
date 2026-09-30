import database as db
from datetime import date, timedelta
import random

db.initialize_db()
print("[INFO] Populating September 2026 data for students, staff, and admin...")

def get_or_create(username, password, role, name, email, inst_type='general'):
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return row["id"]
    return db.add_user(username, password, role, name, email)

# 1. Create Users
admin_id = get_or_create("admin_new", "admin123", "admin", "System Admin", "admin@ecomess.com")

students = [
    get_or_create(f"student_sep_{i}", "pass123", "student", f"Sep Student {i}", f"stu{i}@test.com", "Institution")
    for i in range(1, 16)
]

staff = [
    get_or_create(f"staff_sep_{i}", "pass123", "staff", f"Sep Staff {i}", f"stf{i}@test.com", "Institution")
    for i in range(1, 11)
]

# 2. Populate Menu for September 2026
# Let's add a menu for the week of Sept 28, 2026 (Monday)
week_start = date(2026, 9, 28)
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
for day in days:
    db.upsert_menu(week_start, day, 'Breakfast', 'Idli, Sambar, Chutney')
    db.upsert_menu(week_start, day, 'Lunch', 'Rice, Dal, Roti, Sabzi')
    db.upsert_menu(week_start, day, 'Snacks', 'Tea, Samosa')
    db.upsert_menu(week_start, day, 'Dinner', 'Roti, Paneer, Dal Makhani')

# 3. Populate Attendance and Polls for September 2026 (Sept 1 to Sept 30)
start_date = date(2026, 9, 1)
end_date = date(2026, 9, 30)
delta = end_date - start_date

food_options_b = ['Idli, Sambar', 'Poha', 'Aloo Paratha']
food_options_l = ['Rice, Dal', 'Veg Biryani', 'Chole Bhature']
food_options_s = ['Tea, Samosa', 'Coffee, Biscuits', 'Juice, Sandwich']
food_options_d = ['Roti, Paneer', 'Veg Pulao', 'Rajma Chawal']

for i in range(delta.days + 1):
    current_date = start_date + timedelta(days=i)
    
    # Staff Attendance
    for stf in staff:
        status = random.choice(['present', 'present', 'present', 'absent'])
        check_in = '07:00:00' if status == 'present' else None
        check_out = '16:00:00' if status == 'present' else None
        db.upsert_attendance(stf, current_date, status, check_in, check_out)
        
    # Student Attendance & Polls
    for stu in students:
        status = random.choice(['present', 'present', 'absent'])
        check_in = '08:00:00' if status == 'present' else None
        check_out = '20:00:00' if status == 'present' else None
        db.upsert_attendance(stu, current_date, status, check_in, check_out)
        
        # 4-meal poll
        db.submit_meal_poll(
            stu, current_date,
            random.choice(food_options_b),
            random.choice(food_options_l),
            random.choice(food_options_s),
            random.choice(food_options_d)
        )

# 4. Generate Mess Bills for September
for stu in students:
    db.generate_monthly_bill(stu, 9, 2026)

print("[OK] September 2026 test data successfully populated!")
