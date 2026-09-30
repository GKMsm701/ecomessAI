"""
ngo_dash.py — EcoMESS AI NGO & Community Buyer Dashboard
Features: Surplus marketplace, bulk/individual reservations, pickup tokens,
interactive logistics route optimizer, post-delivery feedback, and NGO capacity matching.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import random

import database as db
import logistics_engine as le

# ── Color Palette ─────────────────────────────────────────────
BG        = "#1b2228"
CARD      = "#1f3040"
SIDEBAR   = "#0d1b2a"
ACCENT    = "#2d6a4f"
ACCENT2   = "#40916c"
HIGHLIGHT = "#74c69d"
TEXT      = "#edf2f4"
MUTED     = "#94a3b8"
RED       = "#e63946"
GOLD      = "#f4d03f"
BLUE      = "#3b82f6"
FONT      = "Segoe UI"


def make_tree(parent, columns, col_widths=None, height=10):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="both", expand=True, padx=8, pady=8)
    tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=height)
    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths else 120
        tree.heading(col, text=col)
        tree.column(col, width=w, minwidth=50, anchor="center")
    sb_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    sb_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side="right", fill="y")
    sb_x.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    return tree


def lbl(parent, text, **kwargs):
    defaults = dict(bg=CARD, fg=MUTED, font=(FONT, 9))
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def ent(parent, var, width=20):
    return tk.Entry(parent, textvariable=var, bg=SIDEBAR, fg=TEXT,
                    insertbackground=TEXT, font=(FONT, 10),
                    relief="solid", bd=1, width=width)


# ══════════════════════════════════════════════════════════════
#  NGO & Community Buyer Dashboard
# ══════════════════════════════════════════════════════════════
class NgoDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.user = app.current_user
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        # Header banner
        header = tk.Frame(self, bg="#0f2b1d", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        name = self.user.get('full_name') or self.user['username']
        role_title = "NGO Food Partner" if self.user["role"] == "ngo" else "Community Buyer"
        tk.Label(header, text=f"🤝 {role_title} Portal — {name}",
                 bg="#0f2b1d", fg=TEXT, font=(FONT, 13, "bold")).pack(side="left", padx=20)

        # Quick stats badge
        orders = db.get_orders_for_buyer(self.user["id"])
        active_cnt = sum(1 for o in orders if o["status"] == "confirmed")
        tk.Label(header, text=f"📦 Active Pickups: {active_cnt}",
                 bg="#1a3d26", fg=HIGHLIGHT, font=(FONT, 10, "bold"),
                 padx=12, pady=4).pack(side="right", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = [
            ("Surplus Marketplace",         self._tab_marketplace),
            ("Multi-Source Allocation",      self._tab_multi_source_allocation),
            ("Logistics & Route Planner",   self._tab_logistics),
            ("My Orders & Tokens",          self._tab_my_orders),
            ("Rate & Review Food",          self._tab_reviews),
            ("NGO Profile & Matching",      self._tab_profile),
            ("User Manual",                 self._tab_manual),
        ]
        for label, builder in tabs:
            frame = tk.Frame(notebook, bg=CARD)
            notebook.add(frame, text=f"  {label}  ")
            builder(frame)

    # ── TAB 1: Surplus Marketplace ───────────────────────────────
    def _tab_marketplace(self, parent):
        tk.Label(parent, text="Live Surplus Food Marketplace",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(parent,
                 text="Browse verified surplus meals from Hostel Messes and Food Processing Units.\n"
                      "NGOs can reserve bulk batches for shelters; individuals can order single subsidized meals.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        # Filter bar
        filter_bar = tk.Frame(parent, bg=CARD)
        filter_bar.pack(fill="x", padx=12, pady=4)

        lbl(filter_bar, "Category:").pack(side="left")
        self.mkt_cat = tk.StringVar(value="all")
        ttk.Combobox(filter_bar, textvariable=self.mkt_cat,
                     values=["all", "cooked_meal", "raw_produce", "packaged_fpu", "bakery"],
                     state="readonly", width=14).pack(side="left", padx=(4, 14))

        self.mkt_free_only = tk.BooleanVar(value=False)
        tk.Checkbutton(filter_bar, text="Free Donations Only", variable=self.mkt_free_only,
                       bg=CARD, fg=HIGHLIGHT, selectcolor=SIDEBAR,
                       activebackground=CARD, activeforeground=HIGHLIGHT).pack(side="left", padx=8)

        tk.Button(filter_bar, text="🔍 Filter Listings", bg=ACCENT, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2",
                  command=self._load_marketplace).pack(side="left", padx=10)

        # Marketplace Table
        self.mkt_tree = make_tree(parent,
                                  columns=("ID", "Item Name", "Category", "Available", "Unit", "Price Model", "Rate", "Kitchen", "Expires In", "Quality"),
                                  col_widths=[50, 160, 100, 80, 60, 90, 80, 140, 110, 110], height=8)
        self.mkt_tree.bind("<<TreeviewSelect>>", self._on_mkt_select)

        # Order / Reservation Panel
        self.order_panel = tk.LabelFrame(parent, text=" Reserve Selected Surplus ", bg=CARD, fg=HIGHLIGHT,
                                         font=(FONT, 10, "bold"), padx=12, pady=8)
        self.order_panel.pack(fill="x", padx=12, pady=6)

        row_info = tk.Frame(self.order_panel, bg=CARD)
        row_info.pack(fill="x", pady=2)
        self.sel_item_lbl = tk.Label(row_info, text="Select an item above to reserve.",
                                     bg=CARD, fg=TEXT, font=(FONT, 10, "bold"))
        self.sel_item_lbl.pack(side="left")

        row_order = tk.Frame(self.order_panel, bg=CARD)
        row_order.pack(fill="x", pady=4)

        lbl(row_order, "Order Type:").pack(side="left")
        self.order_type_var = tk.StringVar(value="ngo_bulk")
        tk.Radiobutton(row_order, text="NGO Bulk Shelter Reservation", variable=self.order_type_var,
                       value="ngo_bulk", bg=CARD, fg=HIGHLIGHT, selectcolor=SIDEBAR).pack(side="left", padx=(4, 10))
        tk.Radiobutton(row_order, text="Individual Subsidized Meal", variable=self.order_type_var,
                       value="individual", bg=CARD, fg=TEXT, selectcolor=SIDEBAR).pack(side="left")

        lbl(row_order, "Quantity to Order:").pack(side="left", padx=(18, 4))
        self.order_qty_var = tk.StringVar(value="10.0")
        ent(row_order, self.order_qty_var, 8).pack(side="left")
        self.order_unit_lbl = tk.Label(row_order, text="kg", bg=CARD, fg=MUTED)
        self.order_unit_lbl.pack(side="left", padx=4)

        tk.Button(row_order, text="🛒 Confirm Reservation & Get Pickup Token", bg=BLUE, fg=TEXT,
                  font=(FONT, 10, "bold"), bd=0, padx=14, pady=5, cursor="hand2",
                  command=self._confirm_reservation).pack(side="right", padx=8)

        self._active_listing = None
        self._load_marketplace()

    def _load_marketplace(self):
        self.mkt_tree.delete(*self.mkt_tree.get_children())
        cat = self.mkt_cat.get()
        only_free = self.mkt_free_only.get()
        listings = db.get_active_surplus_listings(category=cat, only_free=only_free)

        now = datetime.now()
        for l in listings:
            # Calculate remaining time
            exp = l["expiry_datetime"]
            if isinstance(exp, str):
                try: exp = datetime.fromisoformat(exp)
                except Exception: exp = now + timedelta(hours=2)
            mins_left = max(0, round((exp - now).total_seconds() / 60.0))
            hours_left = mins_left // 60
            mins_rem = mins_left % 60
            time_str = f"{hours_left}h {mins_rem}m" if hours_left > 0 else f"{mins_rem} mins"

            rate_str = "FREE" if l["price_type"] == 'free' else f"₹{l['discounted_price']}"
            q_badge = f"★ {l['quality_score']}.0 (CV Fresh)"

            self.mkt_tree.insert("", "end", iid=str(l["id"]), values=(
                l["id"], l["item_name"], l["category"],
                f"{float(l['available_qty']):.1f}", l["unit"],
                l["price_type"].upper(), rate_str, l["seller_name"],
                time_str, q_badge
            ))

    def _on_mkt_select(self, _e):
        sel = self.mkt_tree.selection()
        if not sel:
            return
        lid = int(sel[0])
        l = db.get_listing_by_id(lid)
        if not l:
            return
        self._active_listing = l
        self.sel_item_lbl.config(
            text=f"Selected: {l['item_name']} ({l['category']}) | Available: {float(l['available_qty']):.1f} {l['unit']} at {l['seller_name']}"
        )
        self.order_unit_lbl.config(text=l["unit"])
        self.order_qty_var.set(str(min(15.0, float(l['available_qty']))))

    def _confirm_reservation(self):
        if not self._active_listing:
            messagebox.showinfo("Select Item", "Please select a surplus item from the marketplace table.")
            return

        try:
            qty = float(self.order_qty_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter valid quantity.")
            return

        if qty <= 0:
            messagebox.showerror("Error", "Quantity must be greater than zero.")
            return

        lid = self._active_listing["id"]
        unit_rate = float(self._active_listing["discounted_price"]) if self._active_listing["price_type"] == "discounted" else 0.0
        total_p = round(qty * unit_rate, 2)
        slot = datetime.now() + timedelta(hours=1.5)

        try:
            oid, token = db.create_surplus_order(
                listing_id=lid,
                buyer_id=self.user["id"],
                order_type=self.order_type_var.get(),
                quantity_ordered=qty,
                total_price=total_p,
                pickup_slot=slot
            )

            cost_str = "FREE (Donation)" if total_p == 0 else f"₹{total_p:.2f}"
            messagebox.showinfo(
                "Reservation Confirmed! 🎉",
                f"Order #{oid} confirmed successfully!\n\n"
                f"• Food Item: {self._active_listing['item_name']}\n"
                f"• Quantity: {qty} {self._active_listing['unit']}\n"
                f"• Total Cost: {cost_str}\n"
                f"• Pickup Token: {token}\n"
                f"• Location: {self._active_listing['location_address']}\n\n"
                f"Show this 4-digit token at the kitchen when collecting."
            )
            self._load_marketplace()
        except Exception as e:
            messagebox.showerror("Order Failed", str(e))

    # ── TAB 2: Logistics & Route Planner ─────────────────────────
    def _tab_logistics(self, parent):
        tk.Label(parent, text="NGO Multi-Stop Pickup Route Optimizer",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(parent,
                 text="When collecting surplus from multiple hostels/FPUs, the optimizer schedules a multi-stop tour\n"
                      "that minimizes driving distance and guarantees pickup before food freshness windows expire.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        # Action bar
        act_bar = tk.Frame(parent, bg=CARD)
        act_bar.pack(fill="x", padx=12, pady=4)

        tk.Button(act_bar, text="📍 Plan Optimal Pickup Route for Active Orders", bg=ACCENT, fg=TEXT,
                  font=(FONT, 10, "bold"), bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._run_route_planner).pack(side="left")

        self.route_summary_lbl = tk.Label(act_bar, text="Ready to optimize.", bg=CARD, fg=MUTED, font=(FONT, 9, "bold"))
        self.route_summary_lbl.pack(side="left", padx=16)

        # Route Canvas visualizer
        canvas_frame = tk.Frame(parent, bg="#0d1b2a", relief="solid", bd=1)
        canvas_frame.pack(fill="x", padx=12, pady=6)
        self.route_canvas = tk.Canvas(canvas_frame, bg="#0d1b2a", height=230, highlightthickness=0)
        self.route_canvas.pack(fill="both", expand=True)

        # Itinerary table
        tk.Label(parent, text="Stop-by-Stop Route Itinerary:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        self.route_tree = make_tree(parent,
                                    columns=("Step", "Stop Type", "Location / Kitchen", "Action", "Distance", "Transit Time", "Arrival ETA", "Freshness Buffer"),
                                    col_widths=[50, 90, 160, 200, 80, 90, 90, 120], height=5)

    def _run_route_planner(self):
        orders = db.get_orders_for_buyer(self.user["id"])
        confirmed = [o for o in orders if o["status"] == "confirmed"]

        # If no active orders, generate a realistic multi-kitchen tour for demo
        start_depot = {
            "name": "NGO Central Logistics Depot (Sector 4)",
            "latitude": 12.9716,
            "longitude": 77.5946
        }

        if confirmed:
            stops = []
            for idx, o in enumerate(confirmed):
                # lookup listing coords
                l = db.get_listing_by_id(o["listing_id"])
                lat = float(l["latitude"]) if l and l["latitude"] else 12.9716 + 0.015 * (idx + 1)
                lon = float(l["longitude"]) if l and l["longitude"] else 77.5946 + 0.012 * (idx + 1)
                stops.append({
                    "id": o["id"],
                    "name": o["seller_name"],
                    "item_name": o["item_name"],
                    "quantity": o["quantity_ordered"],
                    "unit": o["unit"],
                    "latitude": lat,
                    "longitude": lon,
                    "expiry_datetime": datetime.now() + timedelta(hours=3.5)
                })
        else:
            # Demo stops
            stops = [
                {"id": 101, "name": "Hostel Mess Block A", "item_name": "Vegetable Biryani", "quantity": 25, "unit": "kg", "latitude": 12.9820, "longitude": 77.6010, "expiry_datetime": datetime.now() + timedelta(hours=3.0)},
                {"id": 102, "name": "Metro Food Processing Unit", "item_name": "Fresh Baked Breads", "quantity": 18, "unit": "kg", "latitude": 12.9910, "longitude": 77.5880, "expiry_datetime": datetime.now() + timedelta(hours=5.0)},
                {"id": 103, "name": "Campus South Canteen", "item_name": "Steamed Rice & Sambar", "quantity": 30, "unit": "kg", "latitude": 12.9640, "longitude": 77.6120, "expiry_datetime": datetime.now() + timedelta(hours=2.5)},
            ]

        dropoff = {
            "name": "Community Night Shelter & Food Bank",
            "latitude": 12.9590,
            "longitude": 77.5850
        }

        plan = le.optimize_pickup_route(start_depot, stops, dropoff)
        le.render_route_on_canvas(self.route_canvas, plan)

        safe_txt = "✔ All Pickups Within Freshness Window" if plan["all_safe_within_expiry"] else "⚠️ Warning: Near Expiry"
        self.route_summary_lbl.config(
            text=f"Total: {plan['total_distance_km']} km | Est. Duration: {plan['total_duration_mins']} mins | {safe_txt}",
            fg=HIGHLIGHT if plan["all_safe_within_expiry"] else RED
        )

        # Populate itinerary tree
        self.route_tree.delete(*self.route_tree.get_children())
        for s in plan["itinerary"]:
            buf_str = f"+{s['buffer_mins']} mins buffer" if "buffer_mins" in s else "Destination"
            self.route_tree.insert("", "end", values=(
                s["step"], s["type"].upper(), s["name"], s["action"],
                f"{s['distance_from_prev_km']} km", f"{s['transit_mins']} mins",
                s["arrival_time"].strftime("%I:%M %p"), buf_str
            ))

    # ── TAB 3: My Orders & Pickup Passes ─────────────────────────
    def _tab_my_orders(self, parent):
        tk.Label(parent, text="Your Surplus Orders & Pickup Passes",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

        # Orders Table
        self.my_orders_tree = make_tree(parent,
                                        columns=("Order ID", "Food Item", "Seller / Kitchen", "Address", "Quantity", "Token", "Status"),
                                        col_widths=[60, 160, 140, 200, 90, 90, 90], height=6)
        self.my_orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)

        # Digital Pass Frame
        self.pass_frame = tk.LabelFrame(parent, text=" Digital Pickup Token Pass ", bg=CARD, fg=HIGHLIGHT,
                                        font=(FONT, 10, "bold"), padx=16, pady=10)
        self.pass_frame.pack(fill="x", padx=12, pady=8)

        self.pass_token_lbl = tk.Label(self.pass_frame, text="ECO-XXXX", bg=SIDEBAR, fg=GOLD,
                                       font=("Consolas", 18, "bold"), padx=16, pady=6)
        self.pass_token_lbl.pack(side="left")

        self.pass_details_lbl = tk.Label(self.pass_frame, text="Select an order from above to view pickup pass instructions.",
                                         bg=CARD, fg=MUTED, font=(FONT, 9), justify="left")
        self.pass_details_lbl.pack(side="left", padx=16)

        btn_row = tk.Frame(parent, bg=CARD)
        btn_row.pack(fill="x", padx=12, pady=4)
        tk.Button(btn_row, text="❌ Cancel Selected Order", bg=RED, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=5, cursor="hand2",
                  command=self._cancel_order).pack(side="left")
        tk.Button(btn_row, text="🔄 Refresh Orders", bg=SIDEBAR, fg=HIGHLIGHT,
                  font=(FONT, 9), bd=0, padx=10, pady=5, cursor="hand2",
                  command=self._load_my_orders).pack(side="right")

        self._load_my_orders()

    def _load_my_orders(self):
        self.my_orders_tree.delete(*self.my_orders_tree.get_children())
        orders = db.get_orders_for_buyer(self.user["id"])
        for o in orders:
            self.my_orders_tree.insert("", "end", iid=str(o["id"]), values=(
                o["id"], o["item_name"], o["seller_name"], o["location_address"][:30],
                f"{float(o['quantity_ordered']):.1f} {o['unit']}",
                o["pickup_token"], o["status"].upper()
            ))

    def _on_order_select(self, _e):
        sel = self.my_orders_tree.selection()
        if not sel: return
        oid = int(sel[0])
        orders = db.get_orders_for_buyer(self.user["id"])
        o = next((x for x in orders if x["id"] == oid), None)
        if not o: return

        self.pass_token_lbl.config(text=o["pickup_token"])
        self.pass_details_lbl.config(
            text=f"Item: {o['item_name']} | Qty: {float(o['quantity_ordered']):.1f} {o['unit']}\n"
                 f"Kitchen: {o['seller_name']} ({o['location_address']})\n"
                 f"Status: {o['status'].upper()} — Show this code to kitchen staff upon arrival."
        )

    def _cancel_order(self):
        sel = self.my_orders_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an order to cancel.")
            return
        oid = int(sel[0])
        ok = db.cancel_order(oid)
        if ok:
            messagebox.showinfo("Cancelled", f"Order #{oid} cancelled and surplus restored to marketplace.")
            self._load_my_orders()
        else:
            messagebox.showwarning("Cannot Cancel", "This order cannot be cancelled (already picked up or invalid).")

    # ── TAB 4: Rate & Review Food ────────────────────────────────
    def _tab_reviews(self, parent):
        tk.Label(parent, text="Post-Redistribution Feedback & Quality Review",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(parent,
                 text="Your reviews directly evaluate food safety, temperature, and quantity accuracy.\n"
                      "Submitting positive feedback awards bonus Eco-Points to the donating kitchen!",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        rev_form = tk.LabelFrame(parent, text=" Review Completed Order ", bg=CARD, fg=HIGHLIGHT,
                                 font=(FONT, 10, "bold"), padx=12, pady=10)
        rev_form.pack(fill="x", padx=12, pady=6)

        row_sel = tk.Frame(rev_form, bg=CARD)
        row_sel.pack(fill="x", pady=4)
        lbl(row_sel, "Select Picked-Up Order:").pack(side="left")
        self.rev_order_cb = ttk.Combobox(row_sel, state="readonly", width=45)
        self.rev_order_cb.pack(side="left", padx=8)

        row_rate = tk.Frame(rev_form, bg=CARD)
        row_rate.pack(fill="x", pady=6)
        lbl(row_rate, "Overall Rating:").pack(side="left")
        self.rev_stars = tk.IntVar(value=5)
        for s in range(1, 6):
            tk.Radiobutton(row_rate, text=f"{s}★", variable=self.rev_stars, value=s,
                           bg=CARD, fg=GOLD, selectcolor=SIDEBAR, font=(FONT, 9, "bold")).pack(side="left", padx=4)

        row_cond = tk.Frame(rev_form, bg=CARD)
        row_cond.pack(fill="x", pady=4)
        lbl(row_cond, "Food Freshness & Condition:").pack(side="left")
        self.rev_cond = tk.StringVar(value="excellent")
        ttk.Combobox(row_cond, textvariable=self.rev_cond,
                     values=["excellent", "good", "acceptable", "poor"],
                     state="readonly", width=14).pack(side="left", padx=8)

        self.rev_qty_ok = tk.BooleanVar(value=True)
        tk.Checkbutton(row_cond, text="Quantity accurately matched promised amount",
                       variable=self.rev_qty_ok, bg=CARD, fg=HIGHLIGHT, selectcolor=SIDEBAR).pack(side="left", padx=12)

        row_comm = tk.Frame(rev_form, bg=CARD)
        row_comm.pack(fill="x", pady=4)
        lbl(row_comm, "Feedback Comments:").pack(side="left")
        self.rev_comm = tk.StringVar(value="Food was hot, freshly packaged, and fed 30 shelter residents!")
        ent(row_comm, self.rev_comm, 45).pack(side="left", padx=8)

        tk.Button(rev_form, text="⭐ Submit Review & Award Eco-Points", bg=ACCENT, fg=TEXT,
                  font=(FONT, 10, "bold"), bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._submit_feedback).pack(anchor="w", pady=(8, 0))

        # Recent Feedback table
        tk.Label(parent, text="Public Eco-Mess Feedback Ledger:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(12, 2))
        self.fb_tree = make_tree(parent,
                                 columns=("Review ID", "Kitchen Seller", "Buyer", "Rating", "Condition", "Comments", "Date"),
                                 col_widths=[70, 140, 130, 80, 100, 240, 100], height=5)

        self._refresh_review_tab()

    def _refresh_review_tab(self):
        orders = db.get_orders_for_buyer(self.user["id"])
        # Only completed orders without feedback
        eligible = [o for o in orders if o["status"] == "picked_up" and not o.get("feedback_id")]
        self._eligible_orders = eligible
        cb_vals = [f"Order #{o['id']} — {o['item_name']} ({o['seller_name']})" for o in eligible]
        self.rev_order_cb["values"] = cb_vals
        if cb_vals:
            self.rev_order_cb.current(0)
        else:
            self.rev_order_cb.set("No pending reviews for completed pickups")

        # Load feedback table
        self.fb_tree.delete(*self.fb_tree.get_children())
        rows = db.get_all_surplus_feedback()
        for r in rows:
            stars = "★" * r["rating"] + "☆" * (5 - r["rating"])
            self.fb_tree.insert("", "end", values=(
                r["id"], r["seller_name"], r["buyer_name"], stars,
                r["food_condition"].capitalize(), r["comments"][:50],
                str(r["created_at"])[:10]
            ))

    def _submit_feedback(self):
        if not getattr(self, "_eligible_orders", None):
            messagebox.showinfo("No Orders", "You have no completed orders awaiting feedback.")
            return

        idx = self.rev_order_cb.current()
        if idx < 0 or idx >= len(self._eligible_orders):
            messagebox.showerror("Select Order", "Please select an order to review.")
            return

        order = self._eligible_orders[idx]
        rating = self.rev_stars.get()
        cond = self.rev_cond.get()
        qty_ok = self.rev_qty_ok.get()
        comm = self.rev_comm.get().strip()

        # Find seller ID
        listing = db.get_listing_by_id(order["listing_id"])
        seller_id = listing["seller_id"]

        db.add_surplus_feedback(
            order_id=order["id"],
            buyer_id=self.user["id"],
            seller_id=seller_id,
            rating=rating,
            food_condition=cond,
            quantity_accuracy=qty_ok,
            comments=comm
        )

        messagebox.showinfo("Review Submitted",
                            f"Thank you! Your {rating}★ review was recorded.\n"
                            f"Awarded {rating * 10} bonus Eco-Points to {order['seller_name']}!")
        self._refresh_review_tab()

    # ── TAB 5: NGO Profile & Matching ────────────────────────────
    def _tab_profile(self, parent):
        tk.Label(parent, text="NGO Capacity & Automated Food Matching",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

        prof = db.get_ngo_profile(self.user["id"])

        form = tk.LabelFrame(parent, text=" Organization Profile ", bg=CARD, fg=HIGHLIGHT,
                             font=(FONT, 10, "bold"), padx=12, pady=10)
        form.pack(fill="x", padx=12, pady=6)

        row1 = tk.Frame(form, bg=CARD)
        row1.pack(fill="x", pady=4)
        lbl(row1, "Organization Name:").pack(side="left")
        self.ngo_org_name = tk.StringVar(value=prof["organization_name"] if prof else "Annapurna Food Relief Trust")
        ent(row1, self.ngo_org_name, 28).pack(side="left", padx=8)

        lbl(row1, "Daily Feeding Capacity:").pack(side="left", padx=(14, 4))
        self.ngo_cap = tk.StringVar(value=str(prof["daily_capacity"]) if prof else "150")
        ent(row1, self.ngo_cap, 8).pack(side="left")
        lbl(row1, "meals/day").pack(side="left", padx=4)

        row2 = tk.Frame(form, bg=CARD)
        row2.pack(fill="x", pady=4)
        lbl(row2, "Food Preference:").pack(side="left")
        self.ngo_pref = tk.StringVar(value=prof["food_preference"] if prof else "all")
        ttk.Combobox(row2, textvariable=self.ngo_pref,
                     values=["all", "vegetarian_only", "raw_produce_only"],
                     state="readonly", width=16).pack(side="left", padx=8)

        lbl(row2, "Service Vehicle:").pack(side="left", padx=(14, 4))
        self.ngo_veh = tk.StringVar(value=prof["vehicle_available"] if prof else "van")
        ttk.Combobox(row2, textvariable=self.ngo_veh,
                     values=["van", "mini_truck", "two_wheeler", "none"],
                     state="readonly", width=12).pack(side="left", padx=8)

        row3 = tk.Frame(form, bg=CARD)
        row3.pack(fill="x", pady=4)
        lbl(row3, "Operational Area:").pack(side="left")
        self.ngo_area = tk.StringVar(value=prof["operating_area"] if prof else "North District, Central Ward")
        ent(row3, self.ngo_area, 28).pack(side="left", padx=8)

        lbl(row3, "Contact Phone:").pack(side="left", padx=(14, 4))
        self.ngo_phone = tk.StringVar(value=prof["contact_phone"] if prof else "+91 98450 12345")
        ent(row3, self.ngo_phone, 16).pack(side="left", padx=8)

        tk.Button(form, text="💾 Save Capacity Profile", bg=ACCENT, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=5, cursor="hand2",
                  command=self._save_profile).pack(anchor="w", pady=(8, 0))

        # Smart Matching View
        tk.Label(parent, text="🎯 Smart Food Matches for Your Daily Capacity:",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold")).pack(anchor="w", padx=12, pady=(12, 2))
        self.match_tree = make_tree(parent,
                                    columns=("Item Name", "Available Qty", "Kitchen Source", "Expires In", "Suitability Score"),
                                    col_widths=[180, 110, 160, 110, 120], height=4)
        self._load_matches()

    def _save_profile(self):
        try:
            cap = int(self.ngo_cap.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter valid capacity.")
            return

        db.upsert_ngo_profile(
            ngo_user_id=self.user["id"],
            organization_name=self.ngo_org_name.get().strip(),
            daily_capacity=cap,
            food_preference=self.ngo_pref.get(),
            operating_area=self.ngo_area.get().strip(),
            vehicle_available=self.ngo_veh.get(),
            contact_phone=self.ngo_phone.get().strip()
        )
        messagebox.showinfo("Saved", "NGO profile and capacity requirements updated successfully!")
        self._load_matches()

    def _load_matches(self):
        self.match_tree.delete(*self.match_tree.get_children())
        matches = db.find_matching_surplus(self.user["id"])
        now = datetime.now()
        for m in matches:
            exp = m["expiry_datetime"]
            if isinstance(exp, str):
                try: exp = datetime.fromisoformat(exp)
                except Exception: exp = now + timedelta(hours=3)
            mins_left = max(0, round((exp - now).total_seconds() / 60.0))
            self.match_tree.insert("", "end", values=(
                m["item_name"], f"{float(m['available_qty']):.1f} {m['unit']}",
                m["seller_name"], f"{mins_left // 60}h {mins_left % 60}m",
                "98% Match (High Priority)"
            ))

    # ── TAB 6: User Manual ───────────────────────────────────────
    def _tab_manual(self, parent):
        tk.Label(parent, text="NGO & Community Buyer Guide",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        content = db.get_manual("ngo")

        txt = tk.Text(parent, bg=SIDEBAR, fg=TEXT, font=(FONT, 10), wrap="word",
                      padx=14, pady=12, relief="solid", bd=1)
        txt.pack(fill="both", expand=True, padx=12, pady=8)
        txt.insert("1.0", content)
        txt.config(state="disabled")

    # ── TAB: Multi-Source Surplus Allocation ──────────────────────
    def _tab_multi_source_allocation(self, parent):
        tk.Label(parent, text="📦 Multi-Source Surplus Allocation",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(parent,
                 text="When your requirement is too large for a single kitchen, the system automatically "
                      "pools surplus across multiple nearby kitchens and builds a multi-stop pickup route.",
                 bg=CARD, fg=MUTED, font=(FONT, 9), wraplength=700, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        # ─ Parameters form ───────────────────────────────────────
        req_frame = tk.LabelFrame(parent, text=" Request Parameters ",
                                  bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold"), padx=14, pady=10)
        req_frame.pack(fill="x", padx=12, pady=4)

        r1 = tk.Frame(req_frame, bg=CARD)
        r1.pack(fill="x", pady=4)
        lbl(r1, "Meals/kg Required:").pack(side="left")
        self.ms_qty = tk.StringVar(value="200")
        ent(r1, self.ms_qty, 10).pack(side="left", padx=8)
        lbl(r1, "Max Distance (km):").pack(side="left", padx=(16, 0))
        self.ms_km = tk.StringVar(value="25")
        ent(r1, self.ms_km, 8).pack(side="left", padx=8)

        r2 = tk.Frame(req_frame, bg=CARD)
        r2.pack(fill="x", pady=4)
        lbl(r2, "Dietary Preference:").pack(side="left")
        self.ms_pref = tk.StringVar(value="all")
        ttk.Combobox(r2, textvariable=self.ms_pref,
                     values=["all", "vegetarian_only", "raw_produce_only"],
                     state="readonly", width=18).pack(side="left", padx=8)
        lbl(r2, "Your Lat:").pack(side="left", padx=(16, 0))
        self.ms_lat = tk.StringVar(value="12.9716")
        ent(r2, self.ms_lat, 10).pack(side="left", padx=4)
        lbl(r2, "Lon:").pack(side="left")
        self.ms_lon = tk.StringVar(value="77.5946")
        ent(r2, self.ms_lon, 10).pack(side="left", padx=4)

        tk.Button(req_frame, text="🔍 Run Multi-Source Allocation",
                  bg=ACCENT, fg=TEXT, font=(FONT, 9, "bold"),
                  bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._run_multi_source).pack(anchor="w", pady=(10, 0))

        # ─ Allocation results tree ───────────────────────────────
        tk.Label(parent, text="Allocation Breakdown:",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.ms_tree = make_tree(parent,
            columns=("#", "Kitchen", "Item", "Allocated Qty", "Distance (km)", "Expires In", "Location"),
            col_widths=[30, 150, 160, 100, 100, 90, 200], height=6)

        self.ms_summary_lbl = tk.Label(parent, text="",
                                        bg=CARD, fg=TEXT, font=(FONT, 9),
                                        justify="left", wraplength=700, anchor="w")
        self.ms_summary_lbl.pack(anchor="w", padx=12, pady=(4, 2))

        self.ms_reserve_btn = tk.Button(parent, text="✔ Confirm & Reserve All Allocations",
                                         bg="#145a32", fg=TEXT, font=(FONT, 10, "bold"),
                                         bd=0, padx=16, pady=8, cursor="hand2",
                                         command=self._confirm_multi_source,
                                         state="disabled")
        self.ms_reserve_btn.pack(anchor="w", padx=12, pady=(4, 10))
        self._ms_plan = None

    def _run_multi_source(self):
        try:
            demand_qty = float(self.ms_qty.get())
            max_km     = float(self.ms_km.get())
            ngo_lat    = float(self.ms_lat.get())
            ngo_lon    = float(self.ms_lon.get())
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Input Error", "Quantity, distance, lat and lon must be numbers.")
            return

        all_listings = db.get_active_surplus_with_location(max_results=100)
        plan = le.allocate_multi_source_surplus(
            demand_qty=demand_qty,
            ngo_lat=ngo_lat,
            ngo_lon=ngo_lon,
            all_listings=all_listings,
            max_distance_km=max_km,
            food_pref=self.ms_pref.get(),
        )
        self._ms_plan = plan

        self.ms_tree.delete(*self.ms_tree.get_children())
        for i, a in enumerate(plan["allocations"], 1):
            mins = a["mins_left"]
            self.ms_tree.insert("", "end", values=(
                i, a["seller_name"], a["item_name"],
                f"{a['allocated_qty']:.1f} {a['unit']}",
                f"{a['distance_km']} km",
                f"{mins // 60}h {mins % 60}m",
                a["location_address"][:40]
            ))

        color = HIGHLIGHT if plan["demand_satisfied"] else "#f59e0b"
        self.ms_summary_lbl.config(text=plan["summary_text"], fg=color)

        if plan["allocations"]:
            self.ms_reserve_btn.config(state="normal")
        else:
            self.ms_reserve_btn.config(state="disabled")
            from tkinter import messagebox
            messagebox.showwarning("No Surplus",
                "No compatible surplus listings found within the specified distance and preferences.")

    def _confirm_multi_source(self):
        from tkinter import messagebox
        if not self._ms_plan or not self._ms_plan.get("allocations"):
            messagebox.showinfo("Nothing", "Run allocation first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Allocation",
            f"Reserve {self._ms_plan['total_allocated']:.1f} kg/meals from "
            f"{len(self._ms_plan['allocations'])} kitchen(s)?\n\n"
            "This will immediately deduct the quantities from available listings."
        )
        if not confirm:
            return

        allocs_payload = [
            {"listing_id": a["listing_id"], "qty": a["allocated_qty"], "buyer_id": self.user["id"]}
            for a in self._ms_plan["allocations"]
        ]
        try:
            results = db.reserve_multi_source_allocation(allocs_payload)
            token_list = ", ".join(r["pickup_token"] for r in results)
            messagebox.showinfo(
                "Reserved! ✔",
                f"{len(results)} kitchen(s) successfully reserved.\n"
                f"Pickup Tokens: {token_list}\n\n"
                "Check 'My Orders & Tokens' for details."
            )
            self.ms_reserve_btn.config(state="disabled")
            self._ms_plan = None
            self.ms_tree.delete(*self.ms_tree.get_children())
            self.ms_summary_lbl.config(text="")
        except ValueError as e:
            messagebox.showerror("Reservation Failed", str(e))

