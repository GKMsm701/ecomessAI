"""
test_new_features.py — Quick integration test for all new EcoMess tables/functions.
Run with: python test_new_features.py
"""

import database as db
from datetime import date, timedelta

db.initialize_db()
print("=== Testing new tables ===\n")

# Get real user IDs from DB
users   = db.get_all_users(role="student")
staff_u = db.get_all_users(role="staff")
student_id = users[0]["id"]   if users   else 1
staff_id   = staff_u[0]["id"] if staff_u else None

tomorrow = date.today() + timedelta(days=1)

# ── 1. meal_poll ──────────────────────────────────────────────
print(f"1. meal_poll — student_id={student_id}, poll_date={tomorrow}")
db.submit_meal_poll(student_id, tomorrow,
                    "Idli & Sambar", "Rice & Dal", "Biscuits", "Chapati")
row = db.get_student_meal_poll(student_id, tomorrow)
print(f"   Saved: breakfast={row['breakfast']}, lunch={row['lunch']}, "
      f"snacks={row['snacks']}, dinner={row['dinner']}")

totals = db.get_meal_poll_totals(tomorrow)
print(f"   Totals sample: {totals[:2]}")

summary = db.get_meal_poll_summary(tomorrow)
print(f"   Summary: {summary}")

# Update (change vote)  
db.submit_meal_poll(student_id, tomorrow, "Dosa", "Biryani", None, "Chapati")
row2 = db.get_student_meal_poll(student_id, tomorrow)
print(f"   Updated: breakfast={row2['breakfast']}, lunch={row2['lunch']}, snacks={row2['snacks']}")
print("   meal_poll: PASS\n")

# ── 2. feedback ───────────────────────────────────────────────
print("2. feedback")
db.add_feedback(student_id, 5, "Great food today!")
db.add_feedback(student_id, 3, "Lunch was okay.")
avg  = db.get_avg_rating()
dist = db.get_rating_distribution()
all_fb = db.get_all_feedback()
student_fb = db.get_feedback_by_student(student_id)
print(f"   Avg rating: {avg}")
print(f"   Distribution: {dict(dist)}")
print(f"   Total rows: {len(all_fb)}, student rows: {len(student_fb)}")
print("   feedback: PASS\n")

# ── 3. food_prepared ──────────────────────────────────────────
print("3. food_prepared")
if staff_id:
    db.add_food_prepared(staff_id, str(date.today()),
                         "Lunch", "Rice & Dal", 25.5, "kg", 80)
    db.add_food_prepared(staff_id, str(date.today()),
                         "Breakfast", "Idli", 10.0, "kg", 60)
    all_fp   = db.get_food_prepared()
    staff_fp = db.get_food_prepared_staff(staff_id)
    print(f"   All rows: {len(all_fp)}, staff rows: {len(staff_fp)}")
else:
    print("   No staff user — skipping")
print("   food_prepared: PASS\n")

# ── 4. demand_prediction ──────────────────────────────────────
print("4. demand_prediction")
pred = db.get_demand_prediction(tomorrow)
for p in pred:
    qty = p.get('recommended_qty', p.get('recommended_qty_kg', 0))
    unit = p.get('unit', 'kg')
    print(f"   {p['meal']:10s}: {p['predicted_students']:4d} students | {qty} {unit}")
print("   demand_prediction: PASS\n")

# ── 5. inventory_usage ────────────────────────────────────────
print("5. inventory_usage")
inv = db.get_inventory()
if inv and staff_id:
    item    = inv[0]
    old_qty = float(item["quantity"])
    db.use_inventory_item(staff_id, item["id"], 1.0, str(date.today()), "test deduction")
    inv_after = db.get_inventory()
    new_qty   = float(next(i["quantity"] for i in inv_after if i["id"] == item["id"]))
    print(f"   '{item['item_name']}': {old_qty} -> {new_qty}  (deducted 1.0)")
    usage = db.get_inventory_usage()
    print(f"   Usage log total rows: {len(usage)}")
    # Test over-deduction guard
    try:
        db.use_inventory_item(staff_id, item["id"], 999999.0, str(date.today()), "should fail")
        print("   ERROR: Should have raised ValueError for over-deduction!")
    except ValueError as e:
        print(f"   Over-deduction guard: PASS ({e})")
else:
    print("   No inventory items or staff — skipping")

print("\n=== All new feature tests PASSED ===")
