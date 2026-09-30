"""
logistics_engine.py — EcoMESS AI NGO Logistics & Route Optimizer
Provides route optimization, distance calculations, food expiry safety checks,
and graphical route visualization for NGO pickup vehicles.
"""

import math
from datetime import datetime, timedelta

# ── Geodesic Distance Helper ──────────────────────────────────
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between two coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def estimate_travel_mins(distance_km, speed_kmh=25.0, stop_handling_mins=10.0):
    """Estimates transit time in minutes given city traffic speed + loading buffer."""
    transit_mins = (distance_km / speed_kmh) * 60.0
    return round(transit_mins + stop_handling_mins, 1)


# ── Nearest-Neighbor Multi-Stop Route Optimizer ───────────────
def optimize_pickup_route(start_node, pickup_nodes, dropoff_node=None, start_time=None):
    """
    Optimizes a multi-stop pickup tour starting from the NGO depot,
    visiting all kitchen pickup stops in optimal sequence, and finishing at the dropoff shelter.
    
    start_node: dict(name, latitude, longitude)
    pickup_nodes: list of dicts(id, name, item_name, quantity, unit, latitude, longitude, expiry_datetime)
    dropoff_node: optional dict(name, latitude, longitude); defaults to start_node
    """
    if not start_time:
        start_time = datetime.now()
    if not dropoff_node:
        dropoff_node = dict(name="NGO Community Shelter / Distribution Hub",
                            latitude=start_node.get("latitude", 12.9716) - 0.015,
                            longitude=start_node.get("longitude", 77.5946) + 0.012)

    unvisited = list(pickup_nodes)
    current_pos = (start_node["latitude"], start_node["longitude"])
    current_time = start_time

    itinerary = []
    # Start waypoint
    itinerary.append({
        "step": 1,
        "type": "start",
        "name": start_node["name"],
        "action": "Vehicle Departure",
        "latitude": start_node["latitude"],
        "longitude": start_node["longitude"],
        "arrival_time": current_time,
        "distance_from_prev_km": 0.0,
        "transit_mins": 0.0,
        "status": "on_schedule"
    })

    step_counter = 2
    total_dist = 0.0
    all_safe = True

    # Nearest Neighbor tour
    while unvisited:
        best_stop = None
        best_dist = float("inf")
        best_idx = -1

        for idx, stop in enumerate(unvisited):
            d = haversine_distance(current_pos[0], current_pos[1], stop["latitude"], stop["longitude"])
            if d < best_dist:
                best_dist = d
                best_stop = stop
                best_idx = idx

        unvisited.pop(best_idx)
        travel_time = estimate_travel_mins(best_dist)
        current_time += timedelta(minutes=travel_time)
        total_dist += best_dist

        # Check against food expiry
        exp_time = best_stop.get("expiry_datetime")
        is_safe = True
        buffer_mins = 0
        if isinstance(exp_time, str):
            try:
                exp_time = datetime.fromisoformat(exp_time)
            except Exception:
                exp_time = None

        if isinstance(exp_time, datetime):
            buffer_mins = round((exp_time - current_time).total_seconds() / 60.0)
            if buffer_mins < 0:
                is_safe = False
                all_safe = False

        itinerary.append({
            "step": step_counter,
            "type": "pickup",
            "id": best_stop.get("id"),
            "name": best_stop["name"],
            "item_name": best_stop.get("item_name", "Surplus Food"),
            "quantity": best_stop.get("quantity", 0),
            "unit": best_stop.get("unit", "kg"),
            "action": f"Collect {best_stop.get('quantity', 0)} {best_stop.get('unit', 'kg')} of {best_stop.get('item_name')}",
            "latitude": best_stop["latitude"],
            "longitude": best_stop["longitude"],
            "arrival_time": current_time,
            "distance_from_prev_km": best_dist,
            "transit_mins": travel_time,
            "buffer_mins": buffer_mins,
            "is_safe": is_safe
        })
        current_pos = (best_stop["latitude"], best_stop["longitude"])
        step_counter += 1

    # Final dropoff
    final_dist = haversine_distance(current_pos[0], current_pos[1], dropoff_node["latitude"], dropoff_node["longitude"])
    final_time = estimate_travel_mins(final_dist, stop_handling_mins=15.0)
    current_time += timedelta(minutes=final_time)
    total_dist += final_dist

    itinerary.append({
        "step": step_counter,
        "type": "dropoff",
        "name": dropoff_node["name"],
        "action": "Unload Surplus & Begin Beneficiary Feeding",
        "latitude": dropoff_node["latitude"],
        "longitude": dropoff_node["longitude"],
        "arrival_time": current_time,
        "distance_from_prev_km": final_dist,
        "transit_mins": final_time,
        "status": "completed"
    })

    total_trip_mins = round((current_time - start_time).total_seconds() / 60.0)

    return {
        "itinerary": itinerary,
        "total_stops": len(pickup_nodes),
        "total_distance_km": round(total_dist, 2),
        "total_duration_mins": total_trip_mins,
        "departure_time": start_time,
        "completion_time": current_time,
        "all_safe_within_expiry": all_safe
    }


# ── Tkinter Route Canvas Renderer ─────────────────────────────
def render_route_on_canvas(canvas, route_plan, bg="#141e28"):
    """Visualizes the optimized route nodes and path on a Tkinter Canvas."""
    canvas.delete("all")
    w = canvas.winfo_width() or 600
    h = canvas.winfo_height() or 280

    itinerary = route_plan.get("itinerary", [])
    if not itinerary:
        canvas.create_text(w / 2, h / 2, text="No route data available.", fill="#94a3b8", font=("Segoe UI", 11))
        return

    # Extract coordinates to scale to canvas
    lats = [node["latitude"] for node in itinerary]
    lons = [node["longitude"] for node in itinerary]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    pad = 45
    lat_span = (max_lat - min_lat) or 0.01
    lon_span = (max_lon - min_lon) or 0.01

    def to_xy(lat, lon):
        x = pad + (lon - min_lon) / lon_span * (w - 2 * pad)
        y = h - (pad + (lat - min_lat) / lat_span * (h - 2 * pad))
        return x, y

    # Background grid lines
    for i in range(1, 5):
        gx = (w / 5) * i
        canvas.create_line(gx, 0, gx, h, fill="#1c2c3b", dash=(2, 4))
        gy = (h / 5) * i
        canvas.create_line(0, gy, w, gy, fill="#1c2c3b", dash=(2, 4))

    # Draw path connecting nodes
    coords = [to_xy(node["latitude"], node["longitude"]) for node in itinerary]
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        # Route path line
        canvas.create_line(x1, y1, x2, y2, fill="#3ddc84", width=3, smooth=True)
        # Distance text on segment
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        d_val = itinerary[i + 1]["distance_from_prev_km"]
        canvas.create_text(mx, my - 8, text=f"{d_val} km", fill="#a7f3d0", font=("Segoe UI", 8, "bold"))

    # Draw nodes
    for i, node in enumerate(itinerary):
        x, y = coords[i]
        ntype = node["type"]

        if ntype == "start":
            color = "#3b82f6"
            label = "DEPOT"
        elif ntype == "dropoff":
            color = "#ec4899"
            label = "SHELTER"
        else:
            color = "#f59e0b" if not node.get("is_safe", True) else "#10b981"
            label = f"STOP {node['step']-1}"

        # Outer pulse ring
        canvas.create_oval(x - 14, y - 14, x + 14, y + 14, outline=color, width=2)
        # Node circle
        canvas.create_oval(x - 9, y - 9, x + 9, y + 9, fill=color, outline="#edf2f4", width=1.5)
        # Step number inside circle
        canvas.create_text(x, y, text=str(node["step"]), fill="#ffffff", font=("Segoe UI", 8, "bold"))

        # Label above/below node
        offset_y = 20 if i % 2 == 0 else -20
        node_txt = f"{label}: {node['name'][:16]}"
        canvas.create_text(x, y + offset_y, text=node_txt, fill="#edf2f4", font=("Segoe UI", 9, "bold"))

    # Legend in bottom corner
    canvas.create_rectangle(10, h - 35, 260, h - 8, fill="#0d1b2a", outline="#1f3040")
    canvas.create_oval(18, h - 26, 26, h - 18, fill="#3b82f6", outline="")
    canvas.create_text(45, h - 22, text="Depot", fill="#94a3b8", font=("Segoe UI", 8))

    canvas.create_oval(75, h - 26, 83, h - 18, fill="#10b981", outline="")
    canvas.create_text(115, h - 22, text="Kitchen Pickup", fill="#94a3b8", font=("Segoe UI", 8))

    canvas.create_oval(165, h - 26, 173, h - 18, fill="#ec4899", outline="")
    canvas.create_text(205, h - 22, text="Drop-off Center", fill="#94a3b8", font=("Segoe UI", 8))


# ── Multi-Source Surplus Allocation Engine ────────────────────
def allocate_multi_source_surplus(demand_qty, ngo_lat, ngo_lon,
                                   all_listings,
                                   max_distance_km=25.0,
                                   food_pref="all",
                                   unit="kg"):
    """
    Greedy multi-source allocation engine.

    Given a target demand_qty and a list of active surplus listings (with
    lat/lon), this finds the optimal subset of kitchens that together satisfy
    the requirement. Prioritises:
      1. Shortest geodesic distance from NGO depot.
      2. Soonest expiry (urgency-first).
      3. Largest available quantity (less hops).

    Args:
        demand_qty (float): Total meals/kg required by the NGO.
        ngo_lat, ngo_lon (float): NGO depot coordinates.
        all_listings (list[dict]): Each dict must have keys:
            id, item_name, available_qty, unit, expiry_datetime,
            latitude, longitude, seller_name, category, location_address.
        max_distance_km (float): Ignore kitchens farther than this.
        food_pref (str): 'all', 'vegetarian_only', or 'raw_produce_only'.
        unit (str): Unit label for display (default 'kg').

    Returns:
        dict with keys:
            allocations  – list of {listing_id, seller_name, item_name,
                                    allocated_qty, unit, distance_km,
                                    location_address, expiry_datetime}
            total_allocated – float
            demand_satisfied – bool
            pickup_nodes    – list ready for optimize_pickup_route()
            summary_text    – human-readable allocation summary string
    """
    now = datetime.now()

    # ── 1. Filter and score candidates ───────────────────────
    candidates = []
    for listing in all_listings:
        # Skip if not available
        if float(listing.get("available_qty", 0)) <= 0:
            continue
        # Expiry check
        expiry = listing.get("expiry_datetime")
        if isinstance(expiry, str):
            try:
                expiry = datetime.fromisoformat(expiry)
            except Exception:
                expiry = now + timedelta(hours=2)
        if expiry <= now:
            continue
        mins_left = (expiry - now).total_seconds() / 60.0
        if mins_left < 30:              # Less than 30 min remaining — skip
            continue

        # Distance filter
        lat = float(listing.get("latitude", 0))
        lon = float(listing.get("longitude", 0))
        dist = haversine_distance(ngo_lat, ngo_lon, lat, lon)
        if dist > max_distance_km:
            continue

        # Dietary filter
        cat = listing.get("category", "")
        name = (listing.get("item_name") or "").lower()
        if food_pref == "vegetarian_only" and any(w in name for w in ["chicken","mutton","fish","beef","meat","egg"]):
            continue
        if food_pref == "raw_produce_only" and cat != "raw_produce":
            continue

        # Score: distance (lower=better) + urgency (sooner expiry = higher priority)
        urgency_score = max(0, 300 - mins_left)   # the sooner it expires the higher
        distance_score = max(0, max_distance_km - dist) * 2
        candidates.append({
            "listing":  listing,
            "dist_km":  dist,
            "expiry":   expiry,
            "mins_left": mins_left,
            "score":    urgency_score + distance_score,
        })

    # Sort: highest score first (most urgent + closest)
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # ── 2. Greedy allocation ──────────────────────────────────
    remaining = demand_qty
    allocations = []
    pickup_nodes = []
    seq = 1

    for cand in candidates:
        if remaining <= 0:
            break
        listing = cand["listing"]
        avail = float(listing["available_qty"])
        take  = min(avail, remaining)
        remaining -= take

        allocations.append({
            "listing_id":      listing["id"],
            "seller_name":     listing.get("seller_name", ""),
            "item_name":       listing.get("item_name", ""),
            "allocated_qty":   round(take, 2),
            "unit":            listing.get("unit", unit),
            "distance_km":     round(cand["dist_km"], 2),
            "location_address": listing.get("location_address", ""),
            "expiry_datetime": cand["expiry"],
            "mins_left":       int(cand["mins_left"]),
        })
        pickup_nodes.append({
            "id":              listing["id"],
            "name":            listing.get("seller_name", f"Kitchen #{listing['id']}"),
            "item_name":       listing.get("item_name", ""),
            "quantity":        round(take, 2),
            "unit":            listing.get("unit", unit),
            "latitude":        float(listing.get("latitude", ngo_lat)),
            "longitude":       float(listing.get("longitude", ngo_lon)),
            "expiry_datetime": cand["expiry"],
            "sequence":        seq,
        })
        seq += 1

    total_allocated = demand_qty - max(0, remaining)
    satisfied = remaining <= 0

    # ── 3. Build summary text ─────────────────────────────────
    lines = [f"📦 Multi-Source Allocation Plan — {total_allocated:.1f} / {demand_qty:.1f} {unit}"]
    if satisfied:
        lines.append("✅ Demand FULLY SATISFIED across sources below:")
    else:
        lines.append(f"⚠️ Partial — only {total_allocated:.1f} {unit} available within {max_distance_km} km")
    for i, a in enumerate(allocations, 1):
        exp_str = a["expiry_datetime"].strftime("%H:%M") if hasattr(a["expiry_datetime"], "strftime") else str(a["expiry_datetime"])[:16]
        lines.append(
            f"  {i}. {a['seller_name']} → {a['allocated_qty']} {a['unit']} "
            f"of {a['item_name']} | {a['distance_km']} km away | Expires {exp_str} "
            f"({a['mins_left']} min left)"
        )
    summary = "\n".join(lines)

    return {
        "allocations":      allocations,
        "total_allocated":  round(total_allocated, 2),
        "demand_qty":       demand_qty,
        "demand_satisfied": satisfied,
        "pickup_nodes":     pickup_nodes,
        "summary_text":     summary,
    }
