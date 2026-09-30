"""
database.py — EcoMess Database Layer
All connections, schema creation, and CRUD operations.
Database: ecomess
"""

import mysql.connector
from mysql.connector import Error
import sys
from datetime import date, datetime, timedelta

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "ecomessdbms"
}


# ──────────────────────────────────────────────────────────────
#  Connection
# ──────────────────────────────────────────────────────────────
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Database connection failed: {e}")


# ──────────────────────────────────────────────────────────────
#  Schema Initialisation
# ──────────────────────────────────────────────────────────────
def initialize_db():
    """Creates all tables and seeds default admin."""
    conn = get_connection()
    cursor = conn.cursor()

    tables = [
        # 1. Users
        """
        CREATE TABLE IF NOT EXISTS users (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            username         VARCHAR(100) NOT NULL UNIQUE,
            password         VARCHAR(255) NOT NULL,
            role             ENUM('student','staff','admin','kitchen_fpu','ngo','buyer','middleman') NOT NULL,
            full_name        VARCHAR(150),
            email            VARCHAR(150),
            institution_type VARCHAR(50) DEFAULT 'general',
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 24. Customer Orders (for Private Kitchen / Canteen diners)
        """
        CREATE TABLE IF NOT EXISTS customer_orders (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            kitchen_user_id INT NOT NULL,
            customer_name   VARCHAR(150) NOT NULL DEFAULT 'Walk-in Customer',
            customer_phone  VARCHAR(30) DEFAULT '',
            items_json      TEXT NOT NULL,
            total_amount    DECIMAL(10,2) NOT NULL DEFAULT 0,
            order_status    ENUM('placed','preparing','ready_for_pickup','completed','cancelled') DEFAULT 'placed',
            pickup_token    VARCHAR(20) NOT NULL,
            notes           VARCHAR(255) DEFAULT '',
            ordered_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at    TIMESTAMP NULL,
            FOREIGN KEY (kitchen_user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 2. Attendance
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id     INT NOT NULL,
            att_date    DATE NOT NULL,
            check_in    TIME,
            check_out   TIME,
            status      ENUM('present','absent','late') DEFAULT 'absent',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_user_date (user_id, att_date)
        )
        """,
        # 3. Menu
        """
        CREATE TABLE IF NOT EXISTS menu (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            week_start_date DATE NOT NULL,
            day_of_week     ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
            meal_type       ENUM('Breakfast','Lunch','Snacks','Dinner') NOT NULL,
            items           TEXT,
            UNIQUE KEY uq_menu (week_start_date, day_of_week, meal_type)
        )
        """,
        # 4. Fee Payments (Mess Bills)
        """
        CREATE TABLE IF NOT EXISTS fee_payments (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            student_id      INT NOT NULL,
            month           TINYINT NOT NULL,
            year            YEAR NOT NULL,
            amount          DECIMAL(10,2) NOT NULL,
            fine            DECIMAL(10,2) DEFAULT 0,
            due_date        DATE NOT NULL,
            payment_date    DATE,
            status          ENUM('pending','paid') DEFAULT 'pending',
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_fee_my (student_id, month, year)
        )
        """,
        # 5. Poll
        """
        CREATE TABLE IF NOT EXISTS poll (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            student_id  INT NOT NULL,
            poll_date   DATE NOT NULL,
            food_item   VARCHAR(200) NOT NULL,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_poll (student_id, poll_date)
        )
        """,
        # 6. Notifications
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            title       VARCHAR(200) NOT NULL,
            message     TEXT NOT NULL,
            target_role ENUM('student','staff','all') NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 7. Notification reads
        """
        CREATE TABLE IF NOT EXISTS notification_reads (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            notification_id INT NOT NULL,
            user_id         INT NOT NULL,
            read_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_read (notification_id, user_id)
        )
        """,
        # 8. Complaints / Suggestions
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id     INT NOT NULL,
            message     TEXT NOT NULL,
            status      ENUM('open','reviewed','closed') DEFAULT 'open',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 9. Inventory
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            item_name   VARCHAR(150) NOT NULL UNIQUE,
            quantity    DECIMAL(10,2) DEFAULT 0,
            unit        VARCHAR(50),
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        # 10. Food Waste
        """
        CREATE TABLE IF NOT EXISTS food_waste (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            staff_id    INT NOT NULL,
            waste_date  DATE NOT NULL,
            item_name   VARCHAR(150) NOT NULL,
            quantity    DECIMAL(10,2) NOT NULL,
            unit        VARCHAR(50),
            FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 11. Salary
        """
        CREATE TABLE IF NOT EXISTS salary (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id     INT NOT NULL,
            month       TINYINT NOT NULL,
            year        YEAR NOT NULL,
            amount      DECIMAL(10,2) NOT NULL,
            paid_date   DATE,
            status      ENUM('pending','paid') DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_salary (user_id, month, year)
        )
        """,
        # 12. Forgot password requests
        """
        CREATE TABLE IF NOT EXISTS forgot_password (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id     INT NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_resolved  BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 13. User manual
        """
        CREATE TABLE IF NOT EXISTS user_manual (
            id      INT AUTO_INCREMENT PRIMARY KEY,
            role    VARCHAR(50) NOT NULL UNIQUE,
            content TEXT
        )
        """,
        # 14. Meal Poll (4-meal dish voting — one dish per meal per student per date)
        """
        CREATE TABLE IF NOT EXISTS meal_poll (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            student_id   INT NOT NULL,
            poll_date    DATE NOT NULL,
            breakfast    VARCHAR(200) DEFAULT NULL,
            lunch        VARCHAR(200) DEFAULT NULL,
            snacks       VARCHAR(200) DEFAULT NULL,
            dinner       VARCHAR(200) DEFAULT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_meal_poll (student_id, poll_date)
        )
        """,
        # 15. Feedback (star ratings from students)
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            rating     TINYINT NOT NULL,
            comment    TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 16. Food Prepared (staff records what was cooked each day)
        """
        CREATE TABLE IF NOT EXISTS food_prepared (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            staff_id       INT NOT NULL,
            prep_date      DATE NOT NULL,
            meal_type      ENUM('Breakfast','Lunch','Snacks','Dinner') NOT NULL,
            item_name      VARCHAR(150) NOT NULL,
            quantity_made  DECIMAL(10,2) NOT NULL,
            unit           VARCHAR(50),
            servings       INT DEFAULT 0,
            FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 17. Inventory Usage (staff deducts items daily)
        """
        CREATE TABLE IF NOT EXISTS inventory_usage (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            staff_id    INT NOT NULL,
            item_id     INT NOT NULL,
            used_qty    DECIMAL(10,2) NOT NULL,
            usage_date  DATE NOT NULL,
            note        VARCHAR(255),
            used_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES inventory(id) ON DELETE CASCADE
        )""",
        # 18. Surplus Food & Near-Expiry Listings
        """
        CREATE TABLE IF NOT EXISTS surplus_listings (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            seller_id         INT NOT NULL,
            item_name         VARCHAR(150) NOT NULL,
            category          ENUM('cooked_meal', 'raw_produce', 'packaged_fpu', 'bakery') NOT NULL,
            total_quantity    DECIMAL(10,2) NOT NULL,
            available_qty     DECIMAL(10,2) NOT NULL,
            unit              VARCHAR(50) NOT NULL DEFAULT 'kg',
            expiry_datetime   DATETIME NOT NULL,
            price_type        ENUM('free', 'discounted') NOT NULL DEFAULT 'free',
            original_price    DECIMAL(10,2) DEFAULT 0,
            discounted_price  DECIMAL(10,2) DEFAULT 0,
            location_address  VARCHAR(255) NOT NULL,
            latitude          DECIMAL(10,6) DEFAULT 0,
            longitude         DECIMAL(10,6) DEFAULT 0,
            quality_status    ENUM('pending_cv', 'verified_fresh', 'flagged_risk', 'expired') DEFAULT 'verified_fresh',
            quality_score     TINYINT DEFAULT 5,
            status            ENUM('available', 'reserved', 'completed', 'diverted_biogas', 'diverted_farm') DEFAULT 'available',
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 19. Surplus Orders & Reservations (NGO Bulk + Individual Buyers)
        """
        CREATE TABLE IF NOT EXISTS surplus_orders (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            listing_id        INT NOT NULL,
            buyer_id          INT NOT NULL,
            order_type        ENUM('ngo_bulk', 'individual') NOT NULL,
            quantity_ordered  DECIMAL(10,2) NOT NULL,
            total_price       DECIMAL(10,2) DEFAULT 0,
            pickup_slot       DATETIME NOT NULL,
            pickup_token      VARCHAR(20) NOT NULL UNIQUE,
            status            ENUM('requested', 'confirmed', 'picked_up', 'cancelled') DEFAULT 'confirmed',
            ordered_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id) REFERENCES surplus_listings(id) ON DELETE CASCADE,
            FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 20. Surplus Feedback & Rating System
        """
        CREATE TABLE IF NOT EXISTS surplus_feedback (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            order_id          INT NOT NULL UNIQUE,
            buyer_id          INT NOT NULL,
            seller_id         INT NOT NULL,
            rating            TINYINT NOT NULL,
            food_condition    ENUM('excellent', 'good', 'acceptable', 'poor') NOT NULL,
            quantity_accuracy BOOLEAN DEFAULT TRUE,
            comments          TEXT,
            points_awarded    INT DEFAULT 10,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES surplus_orders(id) ON DELETE CASCADE,
            FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 21. Reward Points Ledger
        """
        CREATE TABLE IF NOT EXISTS reward_points (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            user_id           INT NOT NULL,
            points            INT NOT NULL,
            reason            ENUM('free_donation', 'high_rating_bonus', 'biogas_diversion', 'farm_diversion', 'redemption') NOT NULL,
            reference_id      INT DEFAULT NULL,
            balance_after     INT NOT NULL,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 22. Circular Economy Waste Diversions (Biogas & Farm Waste)
        """
        CREATE TABLE IF NOT EXISTS circular_diversions (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            kitchen_id        INT NOT NULL,
            waste_type        ENUM('unsold_cooked_food', 'spoiled_edible', 'vegetable_scraps', 'fpu_organic_sludge') NOT NULL,
            destination_type  ENUM('biogas_plant', 'organic_farm') NOT NULL,
            partner_name      VARCHAR(150) NOT NULL,
            quantity_kg       DECIMAL(10,2) NOT NULL,
            energy_points     INT DEFAULT 0,
            financial_credit  DECIMAL(10,2) DEFAULT 0,
            status            ENUM('scheduled', 'in_transit', 'processed') DEFAULT 'scheduled',
            diversion_date    DATE NOT NULL,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kitchen_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # 23. NGO Capacity & Requirement Profiles
        """
        CREATE TABLE IF NOT EXISTS ngo_profiles (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            ngo_user_id       INT NOT NULL UNIQUE,
            organization_name VARCHAR(180) NOT NULL,
            daily_capacity    INT NOT NULL DEFAULT 100,
            food_preference   ENUM('all', 'vegetarian_only', 'raw_produce_only') DEFAULT 'all',
            operating_radius  DECIMAL(5,2) DEFAULT 15.0,
            operating_area    VARCHAR(200) NOT NULL,
            vehicle_available ENUM('van', 'mini_truck', 'two_wheeler', 'none') DEFAULT 'van',
            contact_phone     VARCHAR(30),
            FOREIGN KEY (ngo_user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    ]

    for sql in tables:
        cursor.execute(sql)

    # Upgrade users.role and user_manual.role ENUM safely if needed
    try:
        cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('student','staff','admin','kitchen_fpu','ngo','buyer') NOT NULL")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE user_manual MODIFY COLUMN role ENUM('student','staff','admin','kitchen_fpu','ngo','buyer') NOT NULL UNIQUE")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('student','staff','admin','kitchen_fpu','ngo','buyer','middleman') NOT NULL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE user_manual MODIFY COLUMN role VARCHAR(50) NOT NULL")
    except Exception:
        pass

    # Seed admin
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, email)
            VALUES (%s,%s,%s,%s,%s)
        """, ("admin", "admin123", "admin", "System Administrator", "admin@ecomess.com"))

    # Seed middleman organization
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='middleman'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, email, institution_type)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, ("middleman", "admin123", "middleman", "EcoMess Platform Middleman Organization", "middleman@ecomess.org", "general"))

    # Seed user manuals
    for role, content in [
        ("student", "Welcome Student!\n\n1. Check the weekly menu under Menu.\n2. View and pay your monthly food costs under Mess Bill.\n3. Cast your food poll for tomorrow under Poll. You can select the standard item or a Veg Alternative.\n4. Submit complaints or suggestions anytime.\n5. Read admin updates in Notifications."),
        ("staff",   "Welcome Staff Member!\n\n1. See the weekly menu.\n2. View your salary details.\n3. Check daily food count from student polls.\n4. Record food prepared and food wastage each day.\n5. Monitor inventory levels and log daily usage.\n6. Read updates in the Dashboard Manual."),
        ("admin",   "Admin Manual\n\n1. Manage users (add/delete/reset passwords).\n2. Edit the weekly menu.\n3. Manage salary and mess bill records.\n4. Edit inventory.\n5. Review rule-based demand prediction based on historical data.\n6. Review food wastage reports.\n7. Read and respond to student complaints.\n8. Send notifications to students or staff.\n9. Update the user manuals when workflows change."),
        ("kitchen_fpu", "Kitchen & FPU Owner Manual\n\n1. Post surplus food or near-expiry batches (Free for NGOs / Subsidized for individuals).\n2. Run CV Freshness Scan before listing to certify quality.\n3. Review incoming NGO bulk reservations and individual orders.\n4. Verify 4-digit pickup token before handing over food.\n5. Route unconsumed or spoiled food to nearby Biogas Plants or Organic Farms.\n6. Earn Eco-Points for free donations, positive feedback, and waste diversions."),
        ("ngo",     "NGO & Buyer Manual\n\n1. Browse active surplus listings from Hostels and Food Processing Units.\n2. Reserve bulk quantities for shelters or order subsidized meals.\n3. Generate pickup tokens and view kitchen address.\n4. Use the Logistics Route Planner to optimize multi-kitchen pickup tours.\n5. Submit post-delivery feedback on food temperature and quality to award points.\n6. Keep your NGO capacity and vehicle availability updated."),
        ("middleman", "Middleman Platform Organization Manual\n\n1. Coordinate surplus redistribution across Institutional Kitchens and Private Kitchens.\n2. Run Automated Smart Matching to pair registered surplus with NGO/relief demands.\n3. Execute Multi-Source Allocation when single-kitchen surplus is insufficient.\n4. Plan and dispatch optimized pickup and multi-stop delivery routes to platform agents.\n5. Activate Emergency & Disaster Support mode for rapid crisis food aggregation.\n6. Route expired or unsafe food to Composting and Biogas plants for closed-loop zero waste.\n7. Issue monthly sustainability audit reports and green certificates to participating kitchens.")
    ]:
        cursor.execute("""
            INSERT INTO user_manual (role, content)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content)
        """, (role, content))

    conn.commit()
    cursor.close()
    conn.close()


# ──────────────────────────────────────────────────────────────
#  AUTH
# ──────────────────────────────────────────────────────────────
def authenticate(username, password, role):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if role == "admin":
        cur.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s AND role IN ('admin', 'kitchen_fpu')
        """, (username, password))
    elif role == "ngo":
        cur.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s AND role IN ('ngo', 'buyer')
        """, (username, password))
    elif role == "middleman":
        cur.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s AND role='middleman'
        """, (username, password))
    else:
        cur.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s AND role=%s
        """, (username, password, role))
    user = cur.fetchone()
    cur.close(); conn.close()
    return user


# ──────────────────────────────────────────────────────────────
#  USER MANAGEMENT
# ──────────────────────────────────────────────────────────────
def get_all_users(role=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if role:
        cur.execute("SELECT id,username,role,full_name,email,created_at FROM users WHERE role=%s ORDER BY role,full_name", (role,))
    else:
        cur.execute("SELECT id,username,role,full_name,email,created_at FROM users ORDER BY role,full_name")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def add_user(username, password, role, full_name, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, password, role, full_name, email)
        VALUES (%s,%s,%s,%s,%s)
    """, (username, password, role, full_name, email))
    conn.commit()
    uid = cur.lastrowid
    cur.close(); conn.close()
    return uid


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close(); conn.close()


def reset_password(user_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_password, user_id))
    conn.commit()
    cur.close(); conn.close()


def forgot_password_request(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO forgot_password (user_id) VALUES (%s)
    """, (user_id,))
    conn.commit()
    cur.close(); conn.close()


def get_forgot_password_requests():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT fp.id, u.id as user_id, u.username, u.full_name, u.role, fp.requested_at
        FROM forgot_password fp
        JOIN users u ON fp.user_id = u.id
        WHERE fp.is_resolved = FALSE
        ORDER BY fp.requested_at DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def resolve_forgot_password(request_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE forgot_password SET is_resolved=TRUE WHERE id=%s", (request_id,))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  ATTENDANCE
# ──────────────────────────────────────────────────────────────
def get_attendance(user_id=None, role=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if user_id:
        cur.execute("""
            SELECT a.*, u.full_name, u.username, u.role
            FROM attendance a JOIN users u ON a.user_id=u.id
            WHERE a.user_id=%s ORDER BY a.att_date DESC
        """, (user_id,))
    elif role:
        cur.execute("""
            SELECT a.*, u.full_name, u.username, u.role
            FROM attendance a JOIN users u ON a.user_id=u.id
            WHERE u.role=%s ORDER BY a.att_date DESC, u.full_name
        """, (role,))
    else:
        cur.execute("""
            SELECT a.*, u.full_name, u.username, u.role
            FROM attendance a JOIN users u ON a.user_id=u.id
            ORDER BY a.att_date DESC, u.full_name
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def upsert_attendance(user_id, att_date, status, check_in=None, check_out=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attendance (user_id, att_date, status, check_in, check_out)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE status=VALUES(status), check_in=VALUES(check_in), check_out=VALUES(check_out)
    """, (user_id, att_date, status, check_in, check_out))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  MENU
# ──────────────────────────────────────────────────────────────
def get_menu_for_week(week_start_date):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM menu WHERE week_start_date=%s
        ORDER BY FIELD(day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
                 FIELD(meal_type,'Breakfast','Lunch','Snacks','Dinner')
    """, (week_start_date,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def upsert_menu(week_start_date, day_of_week, meal_type, items):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO menu (week_start_date, day_of_week, meal_type, items)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE items=VALUES(items)
    """, (week_start_date, day_of_week, meal_type, items))
    conn.commit()
    cur.close(); conn.close()


def delete_menu_entry(menu_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  MESS BILLS (formerly Fee Payments)
# ──────────────────────────────────────────────────────────────

MEAL_RATES = {'breakfast': 40, 'lunch': 60, 'snacks': 20, 'dinner': 50}
FINE_PER_DAY = 10.0

def generate_monthly_bill(student_id, month, year):
    """Calculates the dynamic mess bill for a student based on meal_poll and records it."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    
    # Calculate costs for the given month and year
    cur.execute("""
        SELECT COUNT(breakfast) as b, COUNT(lunch) as l, 
               COUNT(snacks) as s, COUNT(dinner) as d
        FROM meal_poll
        WHERE student_id=%s AND MONTH(poll_date)=%s AND YEAR(poll_date)=%s
    """, (student_id, month, year))
    counts = cur.fetchone()
    if not counts:
        counts = {'b': 0, 'l': 0, 's': 0, 'd': 0}

    meal_cost = (
        counts['b'] * MEAL_RATES['breakfast'] +
        counts['l'] * MEAL_RATES['lunch'] +
        counts['s'] * MEAL_RATES['snacks'] +
        counts['d'] * MEAL_RATES['dinner']
    )
    
    # Calculate due date: 5th of the following month
    due_month = month + 1 if month < 12 else 1
    due_year = year if month < 12 else year + 1
    due_date = date(due_year, due_month, 5)

    # Check if a bill already exists (to compute fines and avoid overwriting paid bills)
    cur.execute("SELECT * FROM fee_payments WHERE student_id=%s AND month=%s AND year=%s", (student_id, month, year))
    existing_bill = cur.fetchone()

    today = date.today()
    fine = 0.0

    if existing_bill:
        if existing_bill['status'] in ('paid', 'processing'):
            cur.close(); conn.close()
            return  # Do not recalculate if already paid or processing
        # Calculate fine dynamically if past due date
        days_late = (today - existing_bill['due_date']).days
        fine = max(0, days_late * FINE_PER_DAY)
        
        cur.execute("""
            UPDATE fee_payments SET amount=%s, fine=%s, due_date=%s WHERE id=%s
        """, (meal_cost, fine, due_date, existing_bill['id']))
    else:
        # Check fine immediately if creating a past-due bill
        days_late = (today - due_date).days
        fine = max(0, days_late * FINE_PER_DAY)
        
        cur.execute("""
            INSERT INTO fee_payments (student_id, month, year, amount, fine, due_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (student_id, month, year, meal_cost, fine, due_date))

    conn.commit()
    cur.close(); conn.close()

def get_mess_bills(student_id=None):
    """Retrieve all mess bills, generating/updating them first."""
    # First, run generation for current and past 2 months for target users
    today = date.today()
    check_months = [
        (today.month, today.year),
        (today.month - 1 if today.month > 1 else 12, today.year if today.month > 1 else today.year - 1),
        (today.month - 2 if today.month > 2 else 12 + (today.month - 2), today.year if today.month > 2 else today.year - 1)
    ]
    students_to_check = [student_id] if student_id else [u['id'] for u in get_all_users('student')]
    
    for sid in students_to_check:
        for m, y in check_months:
            generate_monthly_bill(sid, m, y)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if student_id:
        cur.execute("""
            SELECT f.*, u.full_name FROM fee_payments f
            JOIN users u ON f.student_id=u.id
            WHERE f.student_id=%s ORDER BY f.year DESC, f.month DESC
        """, (student_id,))
    else:
        cur.execute("""
            SELECT f.*, u.full_name FROM fee_payments f
            JOIN users u ON f.student_id=u.id
            ORDER BY f.year DESC, f.month DESC
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def request_pay_mess_bill(bill_id):
    """Student requests payment, setting status to processing and freezing fine/date."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT due_date FROM fee_payments WHERE id=%s", (bill_id,))
    row = cur.fetchone()
    if row:
        today = date.today()
        days_late = (today - row['due_date']).days
        fine = max(0.0, days_late * FINE_PER_DAY)
        cur.execute("""
            UPDATE fee_payments SET status='processing', payment_date=%s, fine=%s WHERE id=%s
        """, (today, fine, bill_id))
        conn.commit()
    cur.close(); conn.close()

def pay_mess_bill(bill_id):
    """Admin marks bill as paid. Processes from pending or processing."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("SELECT due_date, status FROM fee_payments WHERE id=%s", (bill_id,))
    row = cur.fetchone()
    if row:
        if row['status'] == 'processing':
            cur.execute("UPDATE fee_payments SET status='paid' WHERE id=%s", (bill_id,))
        else:
            today = date.today()
            days_late = (today - row['due_date']).days
            fine = max(0.0, days_late * FINE_PER_DAY)
            cur.execute("""
                UPDATE fee_payments SET status='paid', payment_date=%s, fine=%s WHERE id=%s
            """, (today, fine, bill_id))
        conn.commit()
    cur.close(); conn.close()



# ──────────────────────────────────────────────────────────────
#  POLL
# ──────────────────────────────────────────────────────────────
def submit_poll(student_id, poll_date, food_item):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO poll (student_id, poll_date, food_item)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE food_item=VALUES(food_item)
    """, (student_id, poll_date, food_item))
    conn.commit()
    cur.close(); conn.close()


def get_poll_results(poll_date):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT food_item, COUNT(*) as votes
        FROM poll WHERE poll_date=%s
        GROUP BY food_item ORDER BY votes DESC
    """, (poll_date,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_student_poll(student_id, poll_date):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM poll WHERE student_id=%s AND poll_date=%s", (student_id, poll_date))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


# ──────────────────────────────────────────────────────────────
#  MEAL POLL (4-meal dish voting)
# ──────────────────────────────────────────────────────────────
def submit_meal_poll(student_id, poll_date, breakfast, lunch, snacks, dinner):
    """Upsert a student's 4-meal dish poll for a given date."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO meal_poll (student_id, poll_date, breakfast, lunch, snacks, dinner)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            breakfast=VALUES(breakfast),
            lunch=VALUES(lunch),
            snacks=VALUES(snacks),
            dinner=VALUES(dinner)
    """, (student_id, poll_date, breakfast or None, lunch or None, snacks or None, dinner or None))
    conn.commit()
    cur.close(); conn.close()


def get_student_meal_poll(student_id, poll_date):
    """Return the student's current meal poll row for a date."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM meal_poll WHERE student_id=%s AND poll_date=%s", (student_id, poll_date))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def get_meal_poll_totals(poll_date):
    """Returns vote counts per meal per dish for a given date.
    Result: [{'meal': 'Breakfast', 'dish': 'Idli & Sambar', 'votes': 12}, ...]
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    results = []
    for meal in ('breakfast', 'lunch', 'snacks', 'dinner'):
        cur.execute(f"""
            SELECT %s AS meal, `{meal}` AS dish, COUNT(*) AS votes
            FROM meal_poll
            WHERE poll_date=%s AND `{meal}` IS NOT NULL
            GROUP BY `{meal}`
            ORDER BY votes DESC
        """, (meal.capitalize(), poll_date))
        results.extend(cur.fetchall())
    cur.close(); conn.close()
    return results


def get_meal_poll_summary(poll_date):
    """Returns total headcount per meal for a date.
    Result: {'Breakfast': 45, 'Lunch': 120, 'Snacks': 60, 'Dinner': 100}
    """
    conn = get_connection()
    cur = conn.cursor()
    summary = {}
    for meal in ('breakfast', 'lunch', 'snacks', 'dinner'):
        cur.execute(f"""
            SELECT COUNT(*) FROM meal_poll
            WHERE poll_date=%s AND `{meal}` IS NOT NULL
        """, (poll_date,))
        summary[meal.capitalize()] = cur.fetchone()[0]
    cur.close(); conn.close()
    return summary


# ──────────────────────────────────────────────────────────────
#  FEEDBACK (student star ratings)
# ──────────────────────────────────────────────────────────────
def add_feedback(student_id, rating, comment):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feedback (student_id, rating, comment)
        VALUES (%s, %s, %s)
    """, (student_id, int(rating), comment or None))
    conn.commit()
    cur.close(); conn.close()


def get_all_feedback():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT f.id, f.rating, f.comment, f.created_at,
               u.full_name, u.username
        FROM feedback f
        JOIN users u ON f.student_id = u.id
        ORDER BY f.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_feedback_by_student(student_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM feedback WHERE student_id=%s ORDER BY created_at DESC
    """, (student_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_avg_rating():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT AVG(rating) FROM feedback")
    val = cur.fetchone()[0]
    cur.close(); conn.close()
    return round(float(val), 2) if val else 0.0


def get_rating_distribution():
    """Returns {1: count, 2: count, 3: count, 4: count, 5: count}"""
    conn = get_connection()
    cur = conn.cursor()
    dist = {i: 0 for i in range(1, 6)}
    cur.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating")
    for rating, count in cur.fetchall():
        dist[int(rating)] = count
    cur.close(); conn.close()
    return dist


# ──────────────────────────────────────────────────────────────
#  FOOD PREPARED (staff daily cooking records)
# ──────────────────────────────────────────────────────────────
def add_food_prepared(staff_id, prep_date, meal_type, item_name, quantity_made, unit, servings):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO food_prepared (staff_id, prep_date, meal_type, item_name, quantity_made, unit, servings)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (staff_id, prep_date, meal_type, item_name, float(quantity_made), unit, int(servings)))
    conn.commit()
    cur.close(); conn.close()


def get_food_prepared(from_date=None, to_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT fp.*, u.full_name FROM food_prepared fp
        JOIN users u ON fp.staff_id = u.id
        WHERE 1=1
    """
    params = []
    if from_date:
        query += " AND fp.prep_date >= %s"; params.append(from_date)
    if to_date:
        query += " AND fp.prep_date <= %s"; params.append(to_date)
    query += " ORDER BY fp.prep_date DESC, fp.meal_type"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_food_prepared_staff(staff_id, from_date=None, to_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = "SELECT * FROM food_prepared WHERE staff_id=%s"
    params = [staff_id]
    if from_date:
        query += " AND prep_date >= %s"; params.append(from_date)
    if to_date:
        query += " AND prep_date <= %s"; params.append(to_date)
    query += " ORDER BY prep_date DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ──────────────────────────────────────────────────────────────
#  INVENTORY USAGE (staff item deductions)
# ──────────────────────────────────────────────────────────────
def use_inventory_item(staff_id, item_id, used_qty, usage_date, note=""):
    """Log usage and deduct from inventory quantity."""
    conn = get_connection()
    cur = conn.cursor()
    # Check available quantity
    cur.execute("SELECT quantity, item_name FROM inventory WHERE id=%s", (item_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        raise ValueError("Inventory item not found.")
    available, item_name = row
    if float(used_qty) > float(available):
        cur.close(); conn.close()
        raise ValueError(f"Insufficient stock for '{item_name}'. Available: {available}")
    # Log usage
    cur.execute("""
        INSERT INTO inventory_usage (staff_id, item_id, used_qty, usage_date, note)
        VALUES (%s, %s, %s, %s, %s)
    """, (staff_id, item_id, float(used_qty), usage_date, note or ""))
    # Deduct from inventory
    cur.execute("""
        UPDATE inventory SET quantity = quantity - %s WHERE id = %s
    """, (float(used_qty), item_id))
    conn.commit()
    cur.close(); conn.close()


def get_inventory_usage(from_date=None, to_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT iu.*, u.full_name AS staff_name, i.item_name, i.unit
        FROM inventory_usage iu
        JOIN users u ON iu.staff_id = u.id
        JOIN inventory i ON iu.item_id = i.id
        WHERE 1=1
    """
    params = []
    if from_date:
        query += " AND iu.usage_date >= %s"; params.append(from_date)
    if to_date:
        query += " AND iu.usage_date <= %s"; params.append(to_date)
    query += " ORDER BY iu.used_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ──────────────────────────────────────────────────────────────
#  DEMAND PREDICTION
# ──────────────────────────────────────────────────────────────
def get_demand_prediction(target_date):
    """Predict demand using meal-specific text parsing rules."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    target_weekday_name = target_date.strftime("%A")

    # Fetch the menu items for the target date's weekday
    target_week_start_date = target_date - timedelta(days=target_date.weekday())
    cur.execute("""
        SELECT meal_type, items FROM menu 
        WHERE week_start_date<=%s AND day_of_week=%s 
        ORDER BY week_start_date DESC
    """, (target_week_start_date, target_weekday_name))
    menu_rows = cur.fetchall()
    
    # Store the most recent definition for this day's meals
    day_menu = {}
    for row in menu_rows:
        if row['meal_type'] not in day_menu:
            day_menu[row['meal_type']] = row['items']

    target_headcounts = get_meal_poll_summary(target_date)
    results = []
    meals = ['Breakfast', 'Lunch', 'Snacks', 'Dinner']

    for meal in meals:
        target_count = target_headcounts.get(meal, 0)
        items_display = day_menu.get(meal, "Unknown Item")
        items = items_display.lower()
        
        # Rule-based calculation
        recommended_text = []
        
        if target_count == 0:
            recommended_text.append("0 qty")
        elif "biryani" in items or "biriyani" in items:
            pieces = target_count * 2
            meat_gm = target_count * 150
            rice_gm = target_count * 350
            if meat_gm >= 1000:
                recommended_text.append(f"{pieces}pcs meat ({meat_gm/1000:.1f}kg)")
            else:
                recommended_text.append(f"{pieces}pcs meat ({meat_gm}g)")
            if rice_gm >= 1000:
                recommended_text.append(f"{rice_gm/1000:.1f}kg rice")
            else:
                recommended_text.append(f"{rice_gm}g rice")
                
        elif "dosa" in items or "idli" in items or "appam" in items or "vada" in items or "puttu" in items:
            pcs = int(target_count * 4.5)
            recommended_text.append(f"{pcs} pcs")
            if "sambar" in items or "chutney" in items or "stew" in items or "curry" in items:
                gravy_l = target_count * 0.15
                recommended_text.append(f"{gravy_l:.1f}L gravy/stew")
                
        elif "chapati" in items or "poori" in items or "paratha" in items or "toast" in items:
            pcs = int(target_count * 3.5)
            recommended_text.append(f"{pcs} pcs")
            if "masala" in items or "curry" in items or "dal" in items or "egg" in items:
                gravy_l = target_count * 0.2
                recommended_text.append(f"{gravy_l:.1f}L curry/sides")
                
        elif "rice" in items or "meals" in items or "pongal" in items or "upma" in items:
            rice_gm = target_count * 400
            if rice_gm >= 1000:
                recommended_text.append(f"{rice_gm/1000:.1f}kg rice/main")
            else:
                recommended_text.append(f"{rice_gm}g rice/main")
            if "curry" in items or "dal" in items or "sambar" in items:
                gravy_l = target_count * 0.2
                recommended_text.append(f"{gravy_l:.1f}L gravy/sides")
                
        elif "tea" in items or "coffee" in items or "milk" in items:
            beverage_l = target_count * 0.15
            recommended_text.append(f"{beverage_l:.1f}L beverage")
            if "biscuits" in items or "cake" in items or "snack" in items or "banana" in items or "pav" in items:
                recommended_text.append(f"{target_count * 2} pcs snacks")
            elif "pakoda" in items or "murukku" in items or "chips" in items:
                grams = target_count * 50
                if grams >= 1000:
                    recommended_text.append(f"{grams/1000:.1f}kg snacks")
                else:
                    recommended_text.append(f"{grams}g snacks")
        else:
            # Generic fallback
            kg = target_count * 0.35
            recommended_text.append(f"{kg:.1f}kg total")

        results.append({
            'meal': meal,
            'predicted_students': target_count,
            'recommended_qty': " + ".join(recommended_text),
            'unit': "",
            'items': items_display,
            'based_on_date': None
        })

    cur.close(); conn.close()
    return results


# ──────────────────────────────────────────────────────────────
#  NOTIFICATIONS
# ──────────────────────────────────────────────────────────────
def send_notification(title, message, target_role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notifications (title, message, target_role)
        VALUES (%s,%s,%s)
    """, (title, message, target_role))
    conn.commit()
    cur.close(); conn.close()


def get_notifications(user_role):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM notifications
        WHERE target_role=%s OR target_role='all'
        ORDER BY created_at DESC
    """, (user_role,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_all_notifications():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ──────────────────────────────────────────────────────────────
#  COMPLAINTS
# ──────────────────────────────────────────────────────────────
def add_complaint(user_id, message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO complaints (user_id, message)
        VALUES (%s,%s)
    """, (user_id, message))
    conn.commit()
    cur.close(); conn.close()


def get_complaints(user_id=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if user_id:
        cur.execute("""
            SELECT c.*, u.full_name, u.username FROM complaints c
            JOIN users u ON c.user_id=u.id
            WHERE c.user_id=%s ORDER BY c.created_at DESC
        """, (user_id,))
    else:
        cur.execute("""
            SELECT c.*, u.full_name, u.username, u.role FROM complaints c
            JOIN users u ON c.user_id=u.id
            ORDER BY c.created_at DESC
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def update_complaint_status(complaint_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE complaints SET status=%s WHERE id=%s", (status, complaint_id))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  INVENTORY
# ──────────────────────────────────────────────────────────────
def get_inventory():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM inventory ORDER BY item_name")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def upsert_inventory(item_name, quantity, unit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inventory (item_name, quantity, unit)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE quantity=VALUES(quantity), unit=VALUES(unit)
    """, (item_name, quantity, unit))
    conn.commit()
    cur.close(); conn.close()


def delete_inventory_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id=%s", (item_id,))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  FOOD WASTE
# ──────────────────────────────────────────────────────────────
def add_food_waste(staff_id, waste_date, item_name, quantity, unit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO food_waste (staff_id, waste_date, item_name, quantity, unit)
        VALUES (%s,%s,%s,%s,%s)
    """, (staff_id, waste_date, item_name, quantity, unit))
    conn.commit()
    cur.close(); conn.close()


def get_food_waste(staff_id=None, from_date=None, to_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT fw.*, u.full_name FROM food_waste fw
        JOIN users u ON fw.staff_id=u.id
        WHERE 1=1
    """
    params = []
    if staff_id:
        query += " AND fw.staff_id=%s"; params.append(staff_id)
    if from_date:
        query += " AND fw.waste_date>=%s"; params.append(from_date)
    if to_date:
        query += " AND fw.waste_date<=%s"; params.append(to_date)
    query += " ORDER BY fw.waste_date DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ──────────────────────────────────────────────────────────────
#  SALARY
# ──────────────────────────────────────────────────────────────
def get_salary(user_id=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if user_id:
        cur.execute("""
            SELECT s.*, u.full_name, u.role FROM salary s
            JOIN users u ON s.user_id=u.id
            WHERE s.user_id=%s ORDER BY s.year DESC, s.month DESC
        """, (user_id,))
    else:
        cur.execute("""
            SELECT s.*, u.full_name, u.role FROM salary s
            JOIN users u ON s.user_id=u.id
            ORDER BY s.year DESC, s.month DESC, u.full_name
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def add_salary(user_id, month, year, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO salary (user_id, month, year, amount)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE amount=VALUES(amount)
    """, (user_id, month, year, amount))
    conn.commit()
    cur.close(); conn.close()


def pay_salary(salary_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE salary SET status='paid', paid_date=%s WHERE id=%s
    """, (date.today(), salary_id))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  USER MANUAL
# ──────────────────────────────────────────────────────────────
def get_manual(role):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT content FROM user_manual WHERE role=%s", (role,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row['content'] if row else "No manual available."


def update_manual(role, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_manual (role, content) VALUES (%s,%s)
        ON DUPLICATE KEY UPDATE content=VALUES(content)
    """, (role, content))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  SURPLUS LISTINGS (Kitchen / FPU)
# ──────────────────────────────────────────────────────────────
def add_surplus_listing(seller_id, item_name, category, total_quantity, available_qty, unit,
                        expiry_datetime, price_type='free', original_price=0.0,
                        discounted_price=0.0, location_address='Central Kitchen',
                        latitude=12.9716, longitude=77.5946,
                        quality_status='verified_fresh', quality_score=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO surplus_listings (
            seller_id, item_name, category, total_quantity, available_qty, unit,
            expiry_datetime, price_type, original_price, discounted_price,
            location_address, latitude, longitude, quality_status, quality_score, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'available')
    """, (
        seller_id, item_name, category, total_quantity, available_qty, unit,
        expiry_datetime, price_type, original_price, discounted_price,
        location_address, latitude, longitude, quality_status, quality_score
    ))
    conn.commit()
    listing_id = cur.lastrowid
    cur.close(); conn.close()
    return listing_id


def get_active_surplus_listings(category=None, only_free=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT sl.*, u.full_name AS seller_name, u.email AS seller_email
        FROM surplus_listings sl
        JOIN users u ON sl.seller_id = u.id
        WHERE sl.status = 'available'
          AND sl.available_qty > 0
          AND sl.expiry_datetime > NOW()
    """
    params = []
    if category and category != 'all':
        query += " AND sl.category = %s"
        params.append(category)
    if only_free:
        query += " AND sl.price_type = 'free'"
    query += " ORDER BY sl.expiry_datetime ASC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_kitchen_listings(seller_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM surplus_listings
        WHERE seller_id = %s
        ORDER BY created_at DESC
    """, (seller_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_listing_by_id(listing_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT sl.*, u.full_name AS seller_name
        FROM surplus_listings sl
        JOIN users u ON sl.seller_id = u.id
        WHERE sl.id = %s
    """, (listing_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def update_listing_status(listing_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE surplus_listings SET status = %s WHERE id = %s", (status, listing_id))
    conn.commit()
    cur.close(); conn.close()


def verify_listing_quality(listing_id, status, score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE surplus_listings
        SET quality_status = %s, quality_score = %s
        WHERE id = %s
    """, (status, score, listing_id))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────
#  SURPLUS ORDERS & RESERVATIONS (NGO Bulk & Individual)
# ──────────────────────────────────────────────────────────────
import random

def create_surplus_order(listing_id, buyer_id, order_type, quantity_ordered, total_price, pickup_slot):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Check available stock
    cur.execute("SELECT available_qty, price_type, seller_id, item_name FROM surplus_listings WHERE id = %s FOR UPDATE", (listing_id,))
    listing = cur.fetchone()
    if not listing:
        cur.close(); conn.close()
        raise ValueError("Listing not found.")
    
    avail = float(listing["available_qty"])
    if quantity_ordered > avail:
        cur.close(); conn.close()
        raise ValueError(f"Only {avail} available. Cannot order {quantity_ordered}.")

    # Generate token
    token = f"ECO-{random.randint(1000, 9999)}"

    # Insert order
    cur.execute("""
        INSERT INTO surplus_orders (
            listing_id, buyer_id, order_type, quantity_ordered, total_price,
            pickup_slot, pickup_token, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed')
    """, (listing_id, buyer_id, order_type, quantity_ordered, total_price, pickup_slot, token))
    order_id = cur.lastrowid

    # Deduct quantity
    new_avail = avail - quantity_ordered
    new_status = 'reserved' if new_avail <= 0 else 'available'
    cur.execute("""
        UPDATE surplus_listings
        SET available_qty = %s, status = %s
        WHERE id = %s
    """, (new_avail, new_status, listing_id))

    # If free donation, award initial reward points to seller
    if listing["price_type"] == 'free':
        seller_id = listing["seller_id"]
        pts = int(quantity_ordered * 5)
        # We also record in reward_points
        cur.execute("SELECT balance_after FROM reward_points WHERE user_id = %s ORDER BY id DESC LIMIT 1", (seller_id,))
        last = cur.fetchone()
        current_bal = last["balance_after"] if last else 0
        new_bal = current_bal + pts
        cur.execute("""
            INSERT INTO reward_points (user_id, points, reason, reference_id, balance_after)
            VALUES (%s, %s, 'free_donation', %s, %s)
        """, (seller_id, pts, order_id, new_bal))

    conn.commit()
    cur.close(); conn.close()
    return order_id, token


def get_orders_for_buyer(buyer_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT so.*, sl.item_name, sl.unit, sl.location_address, sl.price_type,
               u.full_name AS seller_name, sf.id AS feedback_id
        FROM surplus_orders so
        JOIN surplus_listings sl ON so.listing_id = sl.id
        JOIN users u ON sl.seller_id = u.id
        LEFT JOIN surplus_feedback sf ON so.id = sf.order_id
        WHERE so.buyer_id = %s
        ORDER BY so.ordered_at DESC
    """, (buyer_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_orders_for_seller(seller_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT so.*, sl.item_name, sl.unit, u.full_name AS buyer_name, u.role AS buyer_role
        FROM surplus_orders so
        JOIN surplus_listings sl ON so.listing_id = sl.id
        JOIN users u ON so.buyer_id = u.id
        WHERE sl.seller_id = %s
        ORDER BY so.ordered_at DESC
    """, (seller_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def complete_pickup_order(order_id, pickup_token=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if pickup_token:
        cur.execute("SELECT id, status FROM surplus_orders WHERE id = %s AND pickup_token = %s", (order_id, pickup_token.strip()))
    else:
        cur.execute("SELECT id, status FROM surplus_orders WHERE id = %s", (order_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        raise ValueError("Invalid pickup token or order ID.")
    
    cur.execute("UPDATE surplus_orders SET status = 'picked_up' WHERE id = %s", (order_id,))
    conn.commit()
    cur.close(); conn.close()
    return True


def cancel_order(order_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT listing_id, quantity_ordered, status FROM surplus_orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    if not order or order["status"] in ('picked_up', 'cancelled'):
        cur.close(); conn.close()
        return False
    
    # Restore quantity
    cur.execute("""
        UPDATE surplus_listings
        SET available_qty = available_qty + %s, status = 'available'
        WHERE id = %s
    """, (order["quantity_ordered"], order["listing_id"]))
    
    cur.execute("UPDATE surplus_orders SET status = 'cancelled' WHERE id = %s", (order_id,))
    conn.commit()
    cur.close(); conn.close()
    return True


# ──────────────────────────────────────────────────────────────
#  FEEDBACK & RATING (Increases Seller Eco-Score)
# ──────────────────────────────────────────────────────────────
def add_surplus_feedback(order_id, buyer_id, seller_id, rating, food_condition, quantity_accuracy=True, comments=""):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    points = int(rating * 10)
    cur.execute("""
        INSERT INTO surplus_feedback (
            order_id, buyer_id, seller_id, rating, food_condition,
            quantity_accuracy, comments, points_awarded
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (order_id, buyer_id, seller_id, rating, food_condition, quantity_accuracy, comments, points))

    # Credit points to seller
    cur.execute("SELECT balance_after FROM reward_points WHERE user_id = %s ORDER BY id DESC LIMIT 1", (seller_id,))
    last = cur.fetchone()
    current_bal = last["balance_after"] if last else 0
    new_bal = current_bal + points
    cur.execute("""
        INSERT INTO reward_points (user_id, points, reason, reference_id, balance_after)
        VALUES (%s, %s, 'high_rating_bonus', %s, %s)
    """, (seller_id, points, order_id, new_bal))

    conn.commit()
    cur.close(); conn.close()
    return True


def get_seller_feedback_stats(seller_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COUNT(*) AS total_reviews, COALESCE(AVG(rating), 5.0) AS avg_rating
        FROM surplus_feedback
        WHERE seller_id = %s
    """, (seller_id,))
    stats = cur.fetchone()
    cur.close(); conn.close()
    return stats


def get_all_surplus_feedback():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT sf.*, u1.full_name AS buyer_name, u2.full_name AS seller_name, so.quantity_ordered
        FROM surplus_feedback sf
        JOIN users u1 ON sf.buyer_id = u1.id
        JOIN users u2 ON sf.seller_id = u2.id
        JOIN surplus_orders so ON sf.order_id = so.id
        ORDER BY sf.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ──────────────────────────────────────────────────────────────
#  REWARD POINTS & ECO-SCORE
# ──────────────────────────────────────────────────────────────
def add_reward_points(user_id, points, reason, reference_id=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT balance_after FROM reward_points WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
    last = cur.fetchone()
    current_bal = last["balance_after"] if last else 0
    new_bal = current_bal + points
    cur.execute("""
        INSERT INTO reward_points (user_id, points, reason, reference_id, balance_after)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, points, reason, reference_id, new_bal))
    conn.commit()
    cur.close(); conn.close()
    return new_bal


def get_user_points(user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT balance_after FROM reward_points WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row["balance_after"] if row else 0


def get_points_history(user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM reward_points
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


# ──────────────────────────────────────────────────────────────
#  CIRCULAR WASTE DIVERSION (Biogas & Organic Farms)
# ──────────────────────────────────────────────────────────────
def record_circular_diversion(kitchen_id, waste_type, destination_type, partner_name,
                              quantity_kg, energy_points=0, financial_credit=0.0, listing_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO circular_diversions (
            kitchen_id, waste_type, destination_type, partner_name,
            quantity_kg, energy_points, financial_credit, diversion_date, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'processed')
    """, (kitchen_id, waste_type, destination_type, partner_name,
          quantity_kg, energy_points, financial_credit, date.today()))
    div_id = cur.lastrowid

    # If associated with a listing, mark it diverted
    if listing_id:
        status_val = 'diverted_biogas' if destination_type == 'biogas_plant' else 'diverted_farm'
        cur.execute("UPDATE surplus_listings SET status = %s, available_qty = 0 WHERE id = %s", (status_val, listing_id))

    # Reward points
    reason_val = 'biogas_diversion' if destination_type == 'biogas_plant' else 'farm_diversion'
    cur.execute("SELECT balance_after FROM reward_points WHERE user_id = %s ORDER BY id DESC LIMIT 1", (kitchen_id,))
    last = cur.fetchone()
    current_bal = last[0] if last else 0
    new_bal = current_bal + energy_points
    cur.execute("""
        INSERT INTO reward_points (user_id, points, reason, reference_id, balance_after)
        VALUES (%s, %s, %s, %s, %s)
    """, (kitchen_id, energy_points, reason_val, div_id, new_bal))

    conn.commit()
    cur.close(); conn.close()
    return div_id


def get_circular_diversions(kitchen_id=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if kitchen_id:
        cur.execute("""
            SELECT cd.*, u.full_name AS kitchen_name
            FROM circular_diversions cd
            JOIN users u ON cd.kitchen_id = u.id
            WHERE cd.kitchen_id = %s
            ORDER BY cd.created_at DESC
        """, (kitchen_id,))
    else:
        cur.execute("""
            SELECT cd.*, u.full_name AS kitchen_name
            FROM circular_diversions cd
            JOIN users u ON cd.kitchen_id = u.id
            ORDER BY cd.created_at DESC
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_sustainability_metrics(kitchen_id=None):
    """Calculates kg food saved, CO2 avoided, and biogas generated."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Food ordered/saved via surplus
    if kitchen_id:
        cur.execute("""
            SELECT COALESCE(SUM(so.quantity_ordered), 0) AS total_kg_redistributed,
                   COUNT(so.id) AS total_orders
            FROM surplus_orders so
            JOIN surplus_listings sl ON so.listing_id = sl.id
            WHERE sl.seller_id = %s AND so.status = 'picked_up'
        """, (kitchen_id,))
    else:
        cur.execute("""
            SELECT COALESCE(SUM(so.quantity_ordered), 0) AS total_kg_redistributed,
                   COUNT(so.id) AS total_orders
            FROM surplus_orders so
            WHERE so.status = 'picked_up'
        """)
    redist = cur.fetchone()

    # Waste diverted
    if kitchen_id:
        cur.execute("""
            SELECT destination_type, COALESCE(SUM(quantity_kg), 0) AS total_kg
            FROM circular_diversions
            WHERE kitchen_id = %s
            GROUP BY destination_type
        """, (kitchen_id,))
    else:
        cur.execute("""
            SELECT destination_type, COALESCE(SUM(quantity_kg), 0) AS total_kg
            FROM circular_diversions
            GROUP BY destination_type
        """)
    div_rows = cur.fetchall()
    cur.close(); conn.close()

    biogas_kg = next((float(r["total_kg"]) for r in div_rows if r["destination_type"] == 'biogas_plant'), 0.0)
    farm_kg = next((float(r["total_kg"]) for r in div_rows if r["destination_type"] == 'organic_farm'), 0.0)
    total_saved = float(redist["total_kg_redistributed"])

    # 1 kg food waste avoided = ~2.5 kg CO2e
    co2_avoided = (total_saved + biogas_kg + farm_kg) * 2.5
    # 1 kg food waste diverted to biogas = ~0.17 m^3 bio-methane
    biogas_m3 = biogas_kg * 0.17

    return {
        "total_food_redistributed_kg": total_saved,
        "meals_served": int(total_saved * 2.5), # ~400g per meal
        "co2_avoided_kg": round(co2_avoided, 1),
        "biogas_diverted_kg": biogas_kg,
        "biogas_m3_generated": round(biogas_m3, 2),
        "farm_compost_kg": farm_kg
    }


# ──────────────────────────────────────────────────────────────
#  NGO PROFILES & SMART MATCHING
# ──────────────────────────────────────────────────────────────
def upsert_ngo_profile(ngo_user_id, organization_name, daily_capacity=100,
                       food_preference='all', operating_radius=15.0,
                       operating_area='City Center', vehicle_available='van',
                       contact_phone=''):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ngo_profiles (
            ngo_user_id, organization_name, daily_capacity, food_preference,
            operating_radius, operating_area, vehicle_available, contact_phone
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            organization_name = VALUES(organization_name),
            daily_capacity    = VALUES(daily_capacity),
            food_preference   = VALUES(food_preference),
            operating_radius  = VALUES(operating_radius),
            operating_area    = VALUES(operating_area),
            vehicle_available = VALUES(vehicle_available),
            contact_phone     = VALUES(contact_phone)
    """, (ngo_user_id, organization_name, daily_capacity, food_preference,
          operating_radius, operating_area, vehicle_available, contact_phone))
    conn.commit()
    cur.close(); conn.close()
    return True


def get_ngo_profile(ngo_user_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM ngo_profiles WHERE ngo_user_id = %s", (ngo_user_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def find_matching_surplus(ngo_user_id):
    """Finds active listings matching the NGO's capacity and dietary preferences."""
    profile = get_ngo_profile(ngo_user_id)
    pref = profile["food_preference"] if profile else 'all'

    listings = get_active_surplus_listings()
    matches = []
    for l in listings:
        score = 100
        # If vegetarian only
        if pref == 'vegetarian_only' and 'meat' in l["item_name"].lower():
            continue
        # Capacity fit
        avail = float(l["available_qty"])
        if profile and avail <= profile["daily_capacity"]:
            score += 20
        matches.append({"listing": l, "match_score": score})
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return [m["listing"] for m in matches]


# ──────────────────────────────────────────────────────────────
#  INSTITUTION TYPE HELPERS
#  institution_type values:
#    Institutional: 'hostel', 'school', 'college', 'midday_meal',
#                   'hospital', 'staff_hostel', 'general'
#    Private Kitchen: 'canteen', 'restaurant', 'catering',
#                     'cloud_kitchen', 'working_womens_hostel', 'cafeteria'
# ──────────────────────────────────────────────────────────────

INSTITUTIONAL_TYPES  = {'hostel', 'school', 'college', 'midday_meal', 'hospital', 'staff_hostel', 'general'}
PRIVATE_KITCHEN_TYPES = {'canteen', 'restaurant', 'catering', 'cloud_kitchen', 'working_womens_hostel', 'cafeteria'}


def get_kitchen_category(institution_type):
    """Returns 'institutional' or 'private_kitchen' for a given institution_type string."""
    if institution_type in PRIVATE_KITCHEN_TYPES:
        return 'private_kitchen'
    return 'institutional'


def update_user_institution_type(user_id, institution_type):
    """Sets the institution_type for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET institution_type = %s WHERE id = %s", (institution_type, user_id))
    conn.commit()
    cur.close(); conn.close()
    return True


# ──────────────────────────────────────────────────────────────
#  CUSTOMER ORDERS (Private Kitchen / Canteen)
# ──────────────────────────────────────────────────────────────

def place_customer_order(kitchen_user_id, customer_name, customer_phone, items_json, total_amount, notes=''):
    """
    Places a food order for a private kitchen diner.
    items_json: list of dicts [{name, qty, price}, ...]
    Returns dict with order_id and pickup_token.
    """
    import random
    token = f"C{random.randint(1000, 9999)}"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customer_orders
            (kitchen_user_id, customer_name, customer_phone, items_json, total_amount, order_status, pickup_token, notes)
        VALUES (%s, %s, %s, %s, %s, 'placed', %s, %s)
    """, (kitchen_user_id, customer_name or 'Walk-in', customer_phone or '',
           str(items_json), total_amount, token, notes or ''))
    conn.commit()
    order_id = cur.lastrowid
    cur.close(); conn.close()
    return {"order_id": order_id, "pickup_token": token, "total_amount": total_amount}


def get_customer_orders(kitchen_user_id=None, status=None, limit=200):
    """Fetches customer orders for a kitchen, optionally filtered by status."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = "SELECT * FROM customer_orders WHERE 1=1"
    params = []
    if kitchen_user_id:
        query += " AND kitchen_user_id = %s"
        params.append(kitchen_user_id)
    if status:
        query += " AND order_status = %s"
        params.append(status)
    query += f" ORDER BY ordered_at DESC LIMIT {int(limit)}"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def update_customer_order_status(order_id, new_status):
    """Updates order status. Sets completed_at when status is 'completed'."""
    conn = get_connection()
    cur = conn.cursor()
    completed_at = datetime.now() if new_status == 'completed' else None
    cur.execute("""
        UPDATE customer_orders
        SET order_status = %s, completed_at = COALESCE(%s, completed_at)
        WHERE id = %s
    """, (new_status, completed_at, order_id))
    conn.commit()
    cur.close(); conn.close()
    return True


def get_customer_order_summary(kitchen_user_id, for_date=None):
    """Returns daily order count and revenue for a kitchen."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if for_date is None:
        for_date = date.today()
    cur.execute("""
        SELECT COUNT(*) AS total_orders,
               COALESCE(SUM(total_amount), 0) AS total_revenue,
               SUM(CASE WHEN order_status = 'completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
               SUM(CASE WHEN order_status IN ('placed','preparing','ready_for_pickup') THEN 1 ELSE 0 END) AS active
        FROM customer_orders
        WHERE kitchen_user_id = %s AND DATE(ordered_at) = %s
    """, (kitchen_user_id, for_date))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row or {"total_orders": 0, "total_revenue": 0, "completed": 0, "cancelled": 0, "active": 0}


# ──────────────────────────────────────────────────────────────
#  MULTI-SOURCE SURPLUS ALLOCATION HELPERS
# ──────────────────────────────────────────────────────────────

def get_active_surplus_with_location(max_results=50, category=None):
    """
    Returns all currently available surplus listings with seller location info.
    Used by the multi-source allocation engine and Middleman control tower.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    q = """
        SELECT sl.*, u.full_name AS seller_name, u.institution_type
        FROM surplus_listings sl
        JOIN users u ON sl.seller_id = u.id
        WHERE sl.status = 'available'
          AND sl.available_qty > 0
          AND sl.expiry_datetime > NOW()
    """
    params = []
    if category and category != 'all':
        q += " AND sl.category = %s"
        params.append(category)
    q += " ORDER BY sl.expiry_datetime ASC LIMIT %s"
    params.append(max_results)
    cur.execute(q, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def reserve_multi_source_allocation(allocations):
    """
    Atomically reserves quantities across multiple listings.
    allocations: list of {listing_id, qty} dicts.
    Returns list of {listing_id, qty, pickup_token} or raises ValueError on conflict.
    """
    import random
    conn = get_connection()
    cur = conn.cursor()
    results = []
    try:
        for alloc in allocations:
            lid = alloc["listing_id"]
            qty = alloc["qty"]
            # Check still available
            cur.execute("SELECT available_qty FROM surplus_listings WHERE id = %s FOR UPDATE", (lid,))
            row = cur.fetchone()
            if not row or row[0] < qty:
                raise ValueError(f"Listing {lid} no longer has enough quantity.")
            # Deduct
            cur.execute("""
                UPDATE surplus_listings
                SET available_qty = available_qty - %s,
                    status = CASE WHEN available_qty - %s <= 0 THEN 'reserved' ELSE status END
                WHERE id = %s
            """, (qty, qty, lid))
            token = f"M{random.randint(10000, 99999)}"
            # Create a surplus order record
            cur.execute("""
                INSERT INTO surplus_orders
                    (listing_id, buyer_id, order_type, quantity_ordered, total_price, pickup_slot, pickup_token, status)
                VALUES (%s, %s, 'ngo_bulk', %s, 0, NOW() + INTERVAL 2 HOUR, %s, 'confirmed')
            """, (lid, alloc["buyer_id"], qty, token))
            results.append({"listing_id": lid, "qty": qty, "pickup_token": token})
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        raise e
    cur.close(); conn.close()
    return results


# ──────────────────────────────────────────────────────────────
#  MONTHLY ESG IMPACT REPORT
# ──────────────────────────────────────────────────────────────

def get_monthly_kitchen_report(seller_id=None, year=None, month=None):
    """
    Generates monthly sustainability report for any kitchen (institutional or private).
    Returns dict with food prepared, waste, surplus redistributed, bio-economy
    diversions, CO2 avoided, cost saved, and eco-points.
    """
    today = date.today()
    if not year:  year  = today.year
    if not month: month = today.month

    conn = get_connection()
    cur  = conn.cursor(dictionary=True)

    # 1. Total Food Prepared
    q = "SELECT COALESCE(SUM(quantity_made),0) AS prep_kg, COALESCE(SUM(servings),0) AS servings FROM food_prepared WHERE YEAR(prep_date)=%s AND MONTH(prep_date)=%s"
    p = [year, month]
    if seller_id:
        q += " AND staff_id=%s"; p.append(seller_id)
    cur.execute(q, p); prep = cur.fetchone() or {"prep_kg": 0, "servings": 0}

    # 2. Food Waste Logged
    q = "SELECT COALESCE(SUM(quantity),0) AS waste_kg FROM food_waste WHERE YEAR(waste_date)=%s AND MONTH(waste_date)=%s"
    p = [year, month]
    if seller_id:
        q += " AND staff_id=%s"; p.append(seller_id)
    cur.execute(q, p); waste = cur.fetchone() or {"waste_kg": 0}

    # 3. Surplus Redistributed
    q = """
        SELECT COALESCE(SUM(so.quantity_ordered),0) AS redist_kg,
               COUNT(DISTINCT so.id) AS orders,
               COALESCE(SUM(CASE WHEN sl.price_type='free' THEN so.quantity_ordered ELSE 0 END),0) AS free_kg,
               COALESCE(SUM(so.total_price),0) AS revenue
        FROM surplus_orders so JOIN surplus_listings sl ON so.listing_id=sl.id
        WHERE YEAR(so.ordered_at)=%s AND MONTH(so.ordered_at)=%s AND so.status='picked_up'
    """
    p = [year, month]
    if seller_id:
        q += " AND sl.seller_id=%s"; p.append(seller_id)
    cur.execute(q, p); surplus = cur.fetchone() or {"redist_kg": 0, "orders": 0, "free_kg": 0, "revenue": 0}

    # 4. Circular Diversions (biogas + farm)
    q = "SELECT destination_type, COALESCE(SUM(quantity_kg),0) AS kg FROM circular_diversions WHERE YEAR(diversion_date)=%s AND MONTH(diversion_date)=%s"
    p = [year, month]
    if seller_id:
        q += " AND kitchen_id=%s"; p.append(seller_id)
    q += " GROUP BY destination_type"
    cur.execute(q, p); cd_rows = cur.fetchall()
    cur.close(); conn.close()

    biogas_kg = sum(float(r["kg"]) for r in cd_rows if r["destination_type"] == "biogas_plant")
    farm_kg   = sum(float(r["kg"]) for r in cd_rows if r["destination_type"] == "organic_farm")

    prep_kg   = float(prep["prep_kg"])
    waste_kg  = float(waste["waste_kg"])
    redist_kg = float(surplus["redist_kg"])
    free_kg   = float(surplus["free_kg"])
    revenue   = float(surplus["revenue"])

    consumed  = max(0.0, prep_kg - waste_kg - redist_kg)
    co2_saved = round((redist_kg + biogas_kg + farm_kg) * 2.5, 1)   # ~2.5 kg CO2 per kg food saved
    cost_saved = round(redist_kg * 45.0 + revenue, 2)               # ~₹45 per meal value

    return {
        "year": year,
        "month": month,
        "food_prepared_kg":        round(prep_kg, 1),
        "estimated_consumption_kg": round(consumed, 1),
        "avoidable_waste_kg":      round(waste_kg, 1),
        "surplus_redistributed_kg": round(redist_kg, 1),
        "free_donations_kg":       round(free_kg, 1),
        "meals_provided":          int(redist_kg * 2.5),
        "revenue_recovered_inr":   revenue,
        "cost_saved_inr":          cost_saved,
        "biogas_diverted_kg":      round(biogas_kg, 1),
        "farm_compost_kg":         round(farm_kg, 1),
        "co2_avoided_kg":          co2_saved,
        "eco_points_earned":       int(free_kg * 10 + redist_kg * 5),
        "completed_orders":        int(surplus["orders"]),
    }


# ──────────────────────────────────────────────────────────────
#  MIDDLEMAN PLATFORM OPERATIONS
# ──────────────────────────────────────────────────────────────

def get_all_surplus_listings_middleman(filter_status=None, category=None):
    """
    Returns all surplus listings with seller and establishment information
    for the Middleman Organization control tower.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    q = """
        SELECT l.*, u.full_name AS seller_name, u.role AS seller_role,
               COALESCE(u.institution_type, 'general') AS seller_institution_type
        FROM surplus_listings l
        LEFT JOIN users u ON l.seller_id = u.id
        WHERE 1=1
    """
    params = []
    if filter_status and filter_status != 'all':
        q += " AND l.status = %s"
        params.append(filter_status)
    if category and category != 'all':
        q += " AND l.category = %s"
        params.append(category)
    q += " ORDER BY l.id DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_middleman_overview_stats():
    """Aggregates platform-wide stats for the Middleman Organization."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT COUNT(*) AS active_count, COALESCE(SUM(available_qty), 0) AS active_kg
        FROM surplus_listings
        WHERE status = 'available' AND expiry_datetime > NOW()
    """)
    active_row = cur.fetchone() or {"active_count": 0, "active_kg": 0}

    cur.execute("""
        SELECT COUNT(*) AS orders_count, COALESCE(SUM(quantity_ordered), 0) AS redist_kg
        FROM surplus_orders
        WHERE status IN ('confirmed', 'picked_up')
    """)
    orders_row = cur.fetchone() or {"orders_count": 0, "redist_kg": 0}

    cur.execute("""
        SELECT COALESCE(SUM(quantity_kg), 0) AS total_diverted_kg
        FROM circular_diversions
    """)
    cd_row = cur.fetchone() or {"total_diverted_kg": 0}

    cur.execute("""
        SELECT COUNT(*) AS total_kitchens
        FROM users
        WHERE role IN ('admin', 'kitchen_fpu')
    """)
    est_row = cur.fetchone() or {"total_kitchens": 0}

    cur.execute("""
        SELECT COUNT(*) AS total_ngos
        FROM users
        WHERE role IN ('ngo', 'buyer')
    """)
    ngo_row = cur.fetchone() or {"total_ngos": 0}

    cur.close(); conn.close()

    redist_kg = float(orders_row["redist_kg"])
    diverted_kg = float(cd_row["total_diverted_kg"])
    co2_saved = round((redist_kg + diverted_kg) * 2.5, 1)

    return {
        "active_listings": int(active_row["active_count"]),
        "active_kg": round(float(active_row["active_kg"]), 1),
        "redistributed_kg": round(redist_kg, 1),
        "meals_provided": int(redist_kg * 2.5),
        "diverted_kg": round(diverted_kg, 1),
        "total_establishments": int(est_row["total_kitchens"]),
        "total_ngos": int(ngo_row["total_ngos"]),
        "co2_saved_kg": co2_saved,
    }


def record_circular_recovery(listing_id, destination_type, partner_name=None, quantity_kg=None, notes=""):
    """
    Diverts unsuitable/expired food to Biogas Plant or Organic Composting Farm.
    Updates listing status and creates a circular_diversions record.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM surplus_listings WHERE id = %s", (listing_id,))
    listing = cur.fetchone()
    if not listing:
        cur.close(); conn.close()
        return False, "Listing not found"

    kg = quantity_kg or float(listing["available_qty"])
    if not partner_name:
        partner_name = "GreenTech Biomethanation Plant" if destination_type == "biogas_plant" else "Greenfield Eco Composting Farm"

    status_listing = "diverted_biogas" if destination_type == "biogas_plant" else "diverted_farm"

    cur.execute("""
        INSERT INTO circular_diversions
        (kitchen_id, waste_type, destination_type, partner_name, quantity_kg, energy_points, financial_credit, status, diversion_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
    """, (
        listing["seller_id"],
        "unsold_cooked_food",
        destination_type,
        partner_name,
        kg,
        int(kg * 12),
        round(kg * 4.5, 2),
        "processed"
    ))

    cur.execute("UPDATE surplus_listings SET status = %s, available_qty = 0 WHERE id = %s", (status_listing, listing_id))
    conn.commit()
    cur.close(); conn.close()
    return True, f"Successfully diverted {kg:.1f} kg to {partner_name} ({destination_type.replace('_',' ').title()})"


def execute_multi_source_allocation(ngo_id, allocations, pickup_slot=None):
    """
    Executes a multi-source allocation batch.
    Creates a surplus_order for each allocated source and decrements available_qty.
    """
    import random
    from datetime import datetime, timedelta
    if not pickup_slot:
        pickup_slot = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    created_orders = []

    try:
        for alloc in allocations:
            listing_id = alloc["listing_id"]
            qty = float(alloc["allocated_qty"])
            cur.execute("SELECT * FROM surplus_listings WHERE id = %s", (listing_id,))
            listing = cur.fetchone()
            if not listing:
                continue

            token = f"{random.randint(1000, 9999)}"
            price = 0.0 if listing["price_type"] == "free" else float(listing["discounted_price"]) * qty

            cur.execute("""
                INSERT INTO surplus_orders
                (listing_id, buyer_id, order_type, quantity_ordered, total_price, pickup_slot, pickup_token, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed')
            """, (listing_id, ngo_id, "ngo_bulk", qty, price, pickup_slot, token))

            order_id = cur.lastrowid

            new_avail = max(0.0, float(listing["available_qty"]) - qty)
            new_status = 'reserved' if new_avail <= 0.01 else 'available'
            cur.execute("UPDATE surplus_listings SET available_qty = %s, status = %s WHERE id = %s",
                        (new_avail, new_status, listing_id))

            created_orders.append({
                "order_id": order_id,
                "listing_id": listing_id,
                "item_name": listing["item_name"],
                "quantity": qty,
                "pickup_token": token,
            })

        conn.commit()
        cur.close(); conn.close()
        return True, created_orders
    except Exception as e:
        conn.rollback()
        cur.close(); conn.close()
        return False, str(e)

