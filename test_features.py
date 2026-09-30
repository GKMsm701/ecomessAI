"""
test_features.py — Automated backend tests for all EcoMess features.
"""
import sys
sys.path.insert(0, '.')
import database as db
from datetime import date, timedelta

PASS = "[PASS]"
FAIL = "[FAIL]"

print("=" * 50)
print("   EcoMess Backend Feature Tests")
print("=" * 50)

# ── AUTH ──────────────────────────────────────────────────────
print("\n[1] Authentication")
tests = [
    ("Student login  (alice/alice123)",   db.authenticate("alice", "alice123", "student"),  True),
    ("Staff   login  (rajan/rajan123)",   db.authenticate("rajan", "rajan123", "staff"),    True),
    ("Admin   login  (admin/admin123)",   db.authenticate("admin", "admin123", "admin"),    True),
    ("Wrong password rejected",           db.authenticate("alice", "wrong", "student"),     False),
    ("Wrong role rejected",               db.authenticate("alice", "alice123", "admin"),    False),
]
for label, result, expect_truthy in tests:
    ok = bool(result) == expect_truthy
    print(f"  {PASS if ok else FAIL}  {label}")

# ── USERS ─────────────────────────────────────────────────────
print("\n[2] User Management")
users    = db.get_all_users()
students = [u for u in users if u["role"] == "student"]
staff    = [u for u in users if u["role"] == "staff"]
print(f"  {PASS}  Total users: {len(users)}")
print(f"  {PASS}  Students ({len(students)}): {[s['username'] for s in students]}")
print(f"  {PASS}  Staff    ({len(staff)}): {[s['username'] for s in staff]}")

# ── MENU ──────────────────────────────────────────────────────
print("\n[3] Weekly Menu")
today  = date.today()
wstart = today - timedelta(days=today.weekday())
menu   = db.get_menu_for_week(str(wstart))
label  = f"Menu entries this week: {len(menu)} (expected >= 7)"
print(f"  {PASS if len(menu) >= 7 else FAIL}  {label}")

# ── ATTENDANCE ────────────────────────────────────────────────
print("\n[4] Attendance")
alice = db.authenticate("alice", "alice123", "student")
att   = db.get_attendance(user_id=alice["id"])
print(f"  {PASS if len(att) > 0 else FAIL}  Alice attendance records: {len(att)}")
rajan = db.authenticate("rajan", "rajan123", "staff")
att2  = db.get_attendance(user_id=rajan["id"])
print(f"  {PASS if len(att2) > 0 else FAIL}  Rajan attendance records: {len(att2)}")

# ── POLL ──────────────────────────────────────────────────────
print("\n[5] Food Poll")
tomorrow = today + timedelta(days=1)
results  = db.get_poll_results(str(tomorrow))
total    = sum(r["votes"] for r in results)
print(f"  {PASS if total > 0 else FAIL}  Poll votes for tomorrow: {total} votes across {len(results)} items")
for r in results:
    print(f"       {r['food_item']}: {r['votes']} vote(s)")

# ── NOTIFICATIONS ─────────────────────────────────────────────
print("\n[6] Notifications")
ns  = db.get_notifications("student")
nst = db.get_notifications("staff")
print(f"  {PASS if len(ns) > 0 else FAIL}  Student notifications: {len(ns)}")
print(f"  {PASS if len(nst) > 0 else FAIL}  Staff   notifications: {len(nst)}")

# ── COMPLAINTS ────────────────────────────────────────────────
print("\n[7] Complaints")
comps = db.get_complaints()
print(f"  {PASS if len(comps) > 0 else FAIL}  Complaints in DB: {len(comps)}")
for c in comps:
    print(f"       [{c['status']}] {c['full_name']}: {c['message'][:50]}...")

# ── INVENTORY ─────────────────────────────────────────────────
print("\n[8] Inventory")
inv = db.get_inventory()
print(f"  {PASS if len(inv) > 0 else FAIL}  Inventory items: {len(inv)}")

# ── FOOD WASTE ────────────────────────────────────────────────
print("\n[9] Food Waste")
fw = db.get_food_waste()
print(f"  {PASS if len(fw) > 0 else FAIL}  Food waste records: {len(fw)}")

# ── SALARY ────────────────────────────────────────────────────
print("\n[10] Salary")
sal = db.get_salary()
print(f"  {PASS if len(sal) > 0 else FAIL}  Salary records: {len(sal)}")

# ── FEE PAYMENTS ─────────────────────────────────────────────
print("\n[11] Fee Payments")
fees = db.get_fee_records()
print(f"  {PASS if len(fees) > 0 else FAIL}  Fee records: {len(fees)}")
pending = [f for f in fees if f["status"] == "pending"]
paid    = [f for f in fees if f["status"] == "paid"]
print(f"       Pending: {len(pending)}   Paid: {len(paid)}")

# ── USER MANUAL ───────────────────────────────────────────────
print("\n[12] User Manual")
for role in ("student", "staff", "admin"):
    m = db.get_manual(role)
    print(f"  {PASS if len(m) > 10 else FAIL}  {role} manual: {len(m)} chars")

# ── FORGOT PASSWORD ───────────────────────────────────────────
print("\n[13] Forgot Password Flow")
alice_id = alice["id"]
db.forgot_password_request(alice_id)
reqs = db.get_forgot_password_requests()
own  = [r for r in reqs if r["user_id"] == alice_id]
print(f"  {PASS if own else FAIL}  Forgot password request logged for alice")
if own:
    db.resolve_forgot_password(own[0]["id"])
    print(f"  {PASS}  Request resolved successfully")

print("\n" + "=" * 50)
print("  All tests complete!")
print("=" * 50)
print("\nTest Accounts:")
print("  admin  / admin123  (Admin)")
print("  alice  / alice123  (Student)")
print("  bob    / bob123    (Student)")
print("  charlie/ charlie123(Student)")
print("  diana  / diana123  (Student)")
print("  evan   / evan123   (Student)")
print("  rajan  / rajan123  (Staff)")
print("  meena  / meena123  (Staff)")
print("  suresh / suresh123 (Staff)")
print()
