"""
seed_kitchen_ngo_data.py — Seeds sample Kitchens, FPUs, NGOs, Buyers,
Surplus Listings, Orders, Reviews, and Circular Waste Diversions.
Run with: python seed_kitchen_ngo_data.py
"""

import database as db
from datetime import datetime, timedelta, date

db.initialize_db()
print("[INFO] Seeding EcoMESS AI Kitchen, NGO, and Logistics Data...")

def get_or_create(username, password, role, name, email):
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return row["id"]
    return db.add_user(username, password, role, name, email)

# 1. Users
k1_id = get_or_create("chef_suresh", "suresh123", "kitchen_fpu", "Chef Suresh - Central Hostel Kitchen", "suresh.kitchen@ecomess.com")
k2_id = get_or_create("metro_fpu", "fpu123", "kitchen_fpu", "Metro Agro Food Processing Ltd", "metro.fpu@ecomess.com")

ngo1_id = get_or_create("annapurna", "ngo123", "ngo", "Annapurna Food Relief Foundation", "contact@annapurna.org")
ngo2_id = get_or_create("hope_shelter", "shelter123", "ngo", "Hope Community Night Shelter", "help@hopeshelter.org")
buyer_id = get_or_create("rahul_buyer", "buyer123", "buyer", "Rahul Verma (Local Buyer)", "rahul.v@gmail.com")

print(f"[OK] Users ready: Kitchens [{k1_id}, {k2_id}], NGOs [{ngo1_id}, {ngo2_id}], Buyer [{buyer_id}]")

# 2. NGO Profiles
db.upsert_ngo_profile(ngo1_id, "Annapurna Food Relief Foundation", daily_capacity=200, food_preference="all", operating_radius=20.0, operating_area="North & Central City", vehicle_available="van", contact_phone="+91 98451 11222")
db.upsert_ngo_profile(ngo2_id, "Hope Community Night Shelter", daily_capacity=80, food_preference="vegetarian_only", operating_radius=12.0, operating_area="East District, Slum Rehabilitation Area", vehicle_available="mini_truck", contact_phone="+91 98452 33444")
print("[OK] NGO Capacity Profiles configured.")

# 3. Active Surplus Listings
now = datetime.now()
l1 = db.add_surplus_listing(
    seller_id=k1_id,
    item_name="Vegetable Biryani & Raita",
    category="cooked_meal",
    total_quantity=40.0,
    available_qty=40.0,
    unit="kg",
    expiry_datetime=now + timedelta(hours=4),
    price_type="free",
    location_address="Hostel Central Mess Block, Campus Gate 2",
    latitude=12.9810, longitude=77.6020,
    quality_status="verified_fresh", quality_score=5
)

l2 = db.add_surplus_listing(
    seller_id=k1_id,
    item_name="Steamed Idli & Hot Sambar",
    category="cooked_meal",
    total_quantity=25.0,
    available_qty=25.0,
    unit="kg",
    expiry_datetime=now + timedelta(hours=3),
    price_type="free",
    location_address="Hostel Central Mess Block, Campus Gate 2",
    latitude=12.9810, longitude=77.6020,
    quality_status="verified_fresh", quality_score=5
)

l3 = db.add_surplus_listing(
    seller_id=k2_id,
    item_name="Whole Wheat Breads & Milk Buns",
    category="bakery",
    total_quantity=50.0,
    available_qty=50.0,
    unit="packets",
    expiry_datetime=now + timedelta(hours=24),
    price_type="discounted",
    original_price=35.0,
    discounted_price=15.0,
    location_address="Metro FPU Plant 3, Industrial Estate",
    latitude=12.9920, longitude=77.5850,
    quality_status="verified_fresh", quality_score=5
)

l4 = db.add_surplus_listing(
    seller_id=k2_id,
    item_name="Packaged Soy Milk & Tofu Packs",
    category="packaged_fpu",
    total_quantity=30.0,
    available_qty=30.0,
    unit="boxes",
    expiry_datetime=now + timedelta(hours=48),
    price_type="discounted",
    original_price=60.0,
    discounted_price=25.0,
    location_address="Metro FPU Plant 3, Industrial Estate",
    latitude=12.9920, longitude=77.5850,
    quality_status="verified_fresh", quality_score=5
)
print("[OK] Surplus Listings published.")

# 4. Completed Sample Order & Feedback
order_id, token = db.create_surplus_order(
    listing_id=l1,
    buyer_id=ngo1_id,
    order_type="ngo_bulk",
    quantity_ordered=15.0,
    total_price=0.0,
    pickup_slot=now + timedelta(hours=1)
)
db.complete_pickup_order(order_id, pickup_token=token)

db.add_surplus_feedback(
    order_id=order_id,
    buyer_id=ngo1_id,
    seller_id=k1_id,
    rating=5,
    food_condition="excellent",
    quantity_accuracy=True,
    comments="Food was steaming hot and fed 45 shelter residents! Thank you Chef Suresh."
)
print(f"[OK] Completed Order #{order_id} with 5-star feedback from Annapurna.")

# 5. Circular Waste Diversions
d1 = db.record_circular_diversion(
    kitchen_id=k1_id,
    waste_type="unsold_cooked_food",
    destination_type="biogas_plant",
    partner_name="GreenPower Biogas Plant #4",
    quantity_kg=40.0,
    energy_points=200,
    financial_credit=0.0
)

d2 = db.record_circular_diversion(
    kitchen_id=k1_id,
    waste_type="vegetable_scraps",
    destination_type="organic_farm",
    partner_name="AgroGreen Organic Valley Farm",
    quantity_kg=60.0,
    energy_points=180,
    financial_credit=240.0
)
print(f"[OK] Circular Waste Diversions logged: Biogas #{d1} (+200 pts) and Farm #{d2} (+180 pts).")

# 6. Check Metrics
metrics = db.get_sustainability_metrics(k1_id)
points = db.get_user_points(k1_id)
print("\n" + "="*50)
print(f"   EcoMESS Kitchen & NGO Seeding Complete!")
print(f"   • Chef Suresh Eco-Points: {points} pts")
print(f"   • Total Food Redistributed: {metrics['total_food_redistributed_kg']} kg")
print(f"   • CO2e Avoided: {metrics['co2_avoided_kg']} kg")
print(f"   • Biogas Energy Generated: {metrics['biogas_m3_generated']} m³")
print("="*50)
