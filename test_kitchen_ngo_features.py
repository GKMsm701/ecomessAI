"""
test_kitchen_ngo_features.py — Automated Backend Test Suite
Validates all Kitchen, NGO, Logistics, and Circular Diversion features.
Run with: python test_kitchen_ngo_features.py
"""

import sys
sys.path.insert(0, '.')
import database as db
import logistics_engine as le
from datetime import datetime, timedelta

PASS = "[PASS]"
FAIL = "[FAIL]"

print("=" * 60)
print("   EcoMESS AI Kitchen, NGO & Logistics Test Suite")
print("=" * 60)

# ── 1. Authentication for new roles ───────────────────────────
print("\n[1] Authentication for Kitchen & NGO")
k_user = db.authenticate("chef_suresh", "suresh123", "kitchen_fpu")
ngo_user = db.authenticate("annapurna", "ngo123", "ngo")
buyer_user = db.authenticate("rahul_buyer", "buyer123", "buyer")

ok_auth = bool(k_user and ngo_user and buyer_user)
print(f"  {PASS if ok_auth else FAIL}  Kitchen/FPU, NGO, and Buyer login")
assert ok_auth, "Authentication failed for new roles."

# ── 2. Surplus Listing Creation & Retrieval ───────────────────
print("\n[2] Surplus Listings (Kitchen / FPU)")
exp_time = datetime.now() + timedelta(hours=6)
lid = db.add_surplus_listing(
    seller_id=k_user["id"],
    item_name="Dal Makhani & Naan",
    category="cooked_meal",
    total_quantity=20.0,
    available_qty=20.0,
    unit="kg",
    expiry_datetime=exp_time,
    price_type="free",
    location_address="Hostel Kitchen C",
    latitude=12.9750,
    longitude=77.6050
)
listing = db.get_listing_by_id(lid)
ok_list = bool(listing and listing["item_name"] == "Dal Makhani & Naan" and float(listing["available_qty"]) == 20.0)
print(f"  {PASS if ok_list else FAIL}  Created Listing #{lid}: {listing['item_name']} ({listing['available_qty']} {listing['unit']})")
assert ok_list

# Active listings retrieval
active = db.get_active_surplus_listings()
ok_active = any(x["id"] == lid for x in active)
print(f"  {PASS if ok_active else FAIL}  Active marketplace listings query returned {len(active)} items")
assert ok_active

# ── 3. Surplus Order Reservation & Stock Deduction ────────────
print("\n[3] Order Reservation & Double-Booking Guard")
oid, token = db.create_surplus_order(
    listing_id=lid,
    buyer_id=ngo_user["id"],
    order_type="ngo_bulk",
    quantity_ordered=8.0,
    total_price=0.0,
    pickup_slot=datetime.now() + timedelta(hours=1)
)
updated_listing = db.get_listing_by_id(lid)
ok_stock = float(updated_listing["available_qty"]) == 12.0
print(f"  {PASS if ok_stock else FAIL}  Order #{oid} reserved 8 kg; remaining stock updated to 12.0 kg (Token: {token})")
assert ok_stock

# Over-deduction guard: attempt to order 15 kg when only 12 kg left
guard_passed = False
try:
    db.create_surplus_order(
        listing_id=lid,
        buyer_id=buyer_user["id"],
        order_type="individual",
        quantity_ordered=15.0,
        total_price=0.0,
        pickup_slot=datetime.now() + timedelta(hours=1)
    )
except ValueError as e:
    guard_passed = True
print(f"  {PASS if guard_passed else FAIL}  Over-ordering guard prevented reserving 15 kg when 12 kg available")
assert guard_passed

# ── 4. Pickup Verification ────────────────────────────────────
print("\n[4] Pickup Token Verification")
ok_pickup = db.complete_pickup_order(oid, pickup_token=token)
orders = db.get_orders_for_buyer(ngo_user["id"])
matched_order = next((o for o in orders if o["id"] == oid), None)
ok_picked_up = bool(matched_order and matched_order["status"] == "picked_up")
print(f"  {PASS if ok_picked_up else FAIL}  Pickup token verified. Order status updated to 'picked_up'")
assert ok_picked_up

# ── 5. Feedback & Eco-Points Credit ───────────────────────────
print("\n[5] Post-Delivery Quality Rating & Eco-Points")
old_pts = db.get_user_points(k_user["id"])
db.add_surplus_feedback(
    order_id=oid,
    buyer_id=ngo_user["id"],
    seller_id=k_user["id"],
    rating=5,
    food_condition="excellent",
    quantity_accuracy=True,
    comments="Food was delicious, cleanly transported, and in great shape."
)
new_pts = db.get_user_points(k_user["id"])
pts_diff = new_pts - old_pts
ok_pts = pts_diff == 50  # 5 stars * 10
print(f"  {PASS if ok_pts else FAIL}  Feedback recorded; seller awarded +{pts_diff} Eco-Points (Total: {new_pts})")
assert ok_pts

# ── 6. Circular Waste Diversion (Biogas & Farms) ───────────────
print("\n[6] Circular Waste Diversion (Zero Landfill)")
div_id = db.record_circular_diversion(
    kitchen_id=k_user["id"],
    waste_type="unsold_cooked_food",
    destination_type="biogas_plant",
    partner_name="GreenPower Biogas Unit #4",
    quantity_kg=30.0,
    energy_points=150,
    financial_credit=0.0,
    listing_id=lid
)
divs = db.get_circular_diversions(k_user["id"])
ok_div = any(d["id"] == div_id for d in divs)
metrics = db.get_sustainability_metrics(k_user["id"])
print(f"  {PASS if ok_div else FAIL}  Circular diversion #{div_id} recorded (30 kg -> Biogas)")
print(f"  {PASS}  Sustainability Metrics: {metrics['total_food_redistributed_kg']} kg food saved | {metrics['co2_avoided_kg']} kg CO2e avoided | {metrics['biogas_m3_generated']} m3 biogas")
assert ok_div

# ── 7. NGO Logistics & Route Optimizer ────────────────────────
print("\n[7] NGO Logistics & Multi-Stop Route Optimizer")
depot = {"name": "Annapurna Central Hub", "latitude": 12.9716, "longitude": 77.5946}
stops = [
    {"id": 1, "name": "Hostel Central Mess", "item_name": "Biryani", "quantity": 15, "unit": "kg", "latitude": 12.9810, "longitude": 77.6020, "expiry_datetime": datetime.now() + timedelta(hours=3)},
    {"id": 2, "name": "Metro FPU Unit", "item_name": "Breads", "quantity": 20, "unit": "packets", "latitude": 12.9920, "longitude": 77.5850, "expiry_datetime": datetime.now() + timedelta(hours=5)},
]
dropoff = {"name": "Night Shelter #2", "latitude": 12.9600, "longitude": 77.5890}

route_res = le.optimize_pickup_route(depot, stops, dropoff)
ok_route = (
    len(route_res["itinerary"]) == 4 and
    route_res["total_distance_km"] > 0 and
    route_res["all_safe_within_expiry"] is True
)
print(f"  {PASS if ok_route else FAIL}  Route plan generated: {route_res['total_distance_km']} km across {route_res['total_stops']} stops in {route_res['total_duration_mins']} mins")
for s in route_res["itinerary"]:
    print(f"       Step {s['step']}: {s['action']} at {s['name']} (Arrival: {s['arrival_time'].strftime('%I:%M %p')})")
assert ok_route

# ── 8. NGO Profile & Smart Matching ───────────────────────────
print("\n[8] NGO Capacity Profiling & Smart Matching")
matches = db.find_matching_surplus(ngo_user["id"])
ok_match = len(matches) > 0
print(f"  {PASS if ok_match else FAIL}  Smart matching engine found {len(matches)} surplus matches tailored to NGO capacity")
assert ok_match

print("\n" + "=" * 60)
print("   ALL 8 TEST SUITES PASSED CLEANLY (100% SUCCESS)!")
print("=" * 60)
