import mysql.connector
import getpass
import sys

# ─────────────────────────────────────────────
#  Database Configuration
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",        # Change to your MySQL username
    "password": "root",        # Change to your MySQL password
    "database": "ecomess"
}

VALID_ROLES = ("student", "staff", "admin")


# ─────────────────────────────────────────────
#  Database Connection
# ─────────────────────────────────────────────
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"\n[ERROR] Cannot connect to database: {err}")
        sys.exit(1)


# ─────────────────────────────────────────────
#  Create Table (run once on first launch)
# ─────────────────────────────────────────────
def initialize_db():
    """Creates the `users` table if it doesn't exist and seeds a default admin."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            username    VARCHAR(100) NOT NULL UNIQUE,
            password    VARCHAR(255) NOT NULL,
            role        ENUM('student', 'staff', 'admin') NOT NULL,
            full_name   VARCHAR(150),
            email       VARCHAR(150),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed a default admin account (password: admin123) if no admin exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, email)
            VALUES (%s, %s, %s, %s, %s)
        """, ("admin", "admin123", "admin", "System Administrator", "admin@eco.com"))
        print("[INFO] Default admin created  →  username: admin | password: admin123")

    conn.commit()
    cursor.close()
    conn.close()


# ─────────────────────────────────────────────
#  Authentication
# ─────────────────────────────────────────────
def authenticate(username: str, password: str, role: str):
    """Returns the user row if credentials match, else None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM users
        WHERE username = %s AND password = %s AND role = %s
    """, (username, password, role))

    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


# ─────────────────────────────────────────────
#  Role-Specific Dashboards
# ─────────────────────────────────────────────
def student_dashboard(user: dict):
    print(f"""
╔══════════════════════════════════════╗
║        STUDENT DASHBOARD             ║
╚══════════════════════════════════════╝
  Welcome, {user['full_name'] or user['username']}!
  Role    : Student
  Email   : {user['email'] or 'N/A'}
  Joined  : {user['created_at'].strftime('%Y-%m-%d') if user.get('created_at') else 'N/A'}

  Options:
    1. View meal schedule
    2. Check balance
    3. Logout
""")
    choice = input("  Enter option: ").strip()
    if choice == "1":
        print("\n  [Meal Schedule] Feature coming soon.\n")
    elif choice == "2":
        print("\n  [Balance] Feature coming soon.\n")
    else:
        print("\n  Logging out...\n")


def staff_dashboard(user: dict):
    print(f"""
╔══════════════════════════════════════╗
║         STAFF DASHBOARD              ║
╚══════════════════════════════════════╝
  Welcome, {user['full_name'] or user['username']}!
  Role    : Staff
  Email   : {user['email'] or 'N/A'}

  Options:
    1. View today's menu
    2. Update meal items
    3. Logout
""")
    choice = input("  Enter option: ").strip()
    if choice == "1":
        print("\n  [Today's Menu] Feature coming soon.\n")
    elif choice == "2":
        print("\n  [Update Menu] Feature coming soon.\n")
    else:
        print("\n  Logging out...\n")


def admin_dashboard(user: dict):
    print(f"""
╔══════════════════════════════════════╗
║         ADMIN DASHBOARD              ║
╚══════════════════════════════════════╝
  Welcome, {user['full_name'] or user['username']}!
  Role    : Administrator

  Options:
    1. List all users
    2. Add new user
    3. Delete a user
    4. Logout
""")
    choice = input("  Enter option: ").strip()

    if choice == "1":
        list_users()
    elif choice == "2":
        add_user()
    elif choice == "3":
        delete_user()
    else:
        print("\n  Logging out...\n")


# ─────────────────────────────────────────────
#  Admin Utilities
# ─────────────────────────────────────────────
def list_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, full_name, email FROM users ORDER BY role")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"\n  {'ID':<5} {'Username':<20} {'Role':<10} {'Full Name':<25} {'Email'}")
    print("  " + "─" * 80)
    for u in users:
        print(f"  {u['id']:<5} {u['username']:<20} {u['role']:<10} "
              f"{(u['full_name'] or ''):<25} {u['email'] or ''}")
    print()


def add_user():
    print("\n  ── Add New User ──")
    username  = input("  Username  : ").strip()
    password  = getpass.getpass("  Password  : ")
    full_name = input("  Full Name : ").strip()
    email     = input("  Email     : ").strip()

    print(f"  Role options: {', '.join(VALID_ROLES)}")
    role = input("  Role      : ").strip().lower()

    if role not in VALID_ROLES:
        print(f"\n  [ERROR] Invalid role. Choose from: {', '.join(VALID_ROLES)}\n")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, email)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password, role, full_name, email))
        conn.commit()
        print(f"\n  [SUCCESS] User '{username}' ({role}) added.\n")
    except mysql.connector.IntegrityError:
        print(f"\n  [ERROR] Username '{username}' already exists.\n")
    finally:
        cursor.close()
        conn.close()


def delete_user():
    list_users()
    try:
        uid = int(input("  Enter user ID to delete (0 to cancel): ").strip())
    except ValueError:
        print("  [ERROR] Invalid ID.\n")
        return

    if uid == 0:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (uid,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()

    if deleted:
        print(f"  [SUCCESS] User ID {uid} deleted.\n")
    else:
        print(f"  [ERROR] No user found with ID {uid}.\n")


# ─────────────────────────────────────────────
#  Login Flow
# ─────────────────────────────────────────────
def login():
    print("""
╔══════════════════════════════════════╗
║       ECO MESS LOGIN SYSTEM          ║
╚══════════════════════════════════════╝
""")
    print(f"  Select Role: {' | '.join(r.capitalize() for r in VALID_ROLES)}")
    role = input("  Role      : ").strip().lower()

    if role not in VALID_ROLES:
        print(f"\n  [ERROR] Invalid role. Please choose from: {', '.join(VALID_ROLES)}\n")
        return False

    username = input("  Username  : ").strip()
    password = getpass.getpass("  Password  : ")

    user = authenticate(username, password, role)

    if user:
        print(f"\n  ✔ Login successful! Welcome, {user['full_name'] or username}.\n")
        if role == "student":
            student_dashboard(user)
        elif role == "staff":
            staff_dashboard(user)
        elif role == "admin":
            admin_dashboard(user)
        return True
    else:
        print("\n  ✘ Invalid credentials or role. Please try again.\n")
        return False


# ─────────────────────────────────────────────
#  Main Entry Point
# ─────────────────────────────────────────────
def main():
    initialize_db()

    while True:
        success = login()

        again = input("  Return to login screen? (y/n): ").strip().lower()
        if again != "y":
            print("\n  Goodbye!\n")
            break


if __name__ == "__main__":
    main()
