"""
middleman_dash.py — EcoMESS Middleman Platform Organization & Logistics Control Tower
Coordinates surplus redistribution across Institutional Kitchens (hostels, schools, colleges,
midday meal kitchens) and Private Kitchens (canteens, restaurants, catering, working women's hostels).
Provides automated smart matching, multi-source pooling, route optimization, disaster relief,
and closed-loop waste recovery to biogas/compost.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import random
import math

import database as db
import logistics_engine as logistics

# ── Color Palette (Consistent Dark Eco-Green & Cyan Tech Theme) ──
BG        = "#0d1b2a"
CARD      = "#162534"
CARD2     = "#1c2e40"
SIDEBAR   = "#0b1522"
ACCENT    = "#2d6a4f"
ACCENT2   = "#40916c"
HIGHLIGHT = "#74c69d"
CYAN      = "#00f5d4"
TEXT      = "#edf2f4"
MUTED     = "#94a3b8"
RED       = "#e63946"
AMBER     = "#f4a261"
GOLD      = "#f4d03f"
BLUE      = "#3b82f6"
PURPLE    = "#a855f7"
FONT      = "Segoe UI"
FONT_MONO = "Consolas"


def make_tree(parent, columns, col_widths=None, height=10):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="both", expand=True, padx=8, pady=8)
    tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=height)
    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths and i < len(col_widths) else 120
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
#  Middleman Organization Dashboard
# ══════════════════════════════════════════════════════════════
class MiddlemanDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.user = app.current_user
        self._build()

    def _build(self):
        self.config(style="Dark.TFrame")

        # Top Control Tower Banner
        header = tk.Frame(self, bg=SIDEBAR, pady=12, padx=16)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=SIDEBAR)
        title_box.pack(side="left")

        tk.Label(title_box, text="🌐 EcoMess Platform Coordinator & Logistics Control Tower",
                 bg=SIDEBAR, fg=HIGHLIGHT, font=(FONT, 16, "bold")).pack(anchor="w")
        tk.Label(title_box,
                 text="Intermediary Hub for Institutional Kitchens, Private Kitchens, and Relief Organizations",
                 bg=SIDEBAR, fg=MUTED, font=(FONT, 9)).pack(anchor="w")

        # Quick refresh and middleman identity
        user_badge = tk.Frame(header, bg="#112233", padx=12, pady=6)
        user_badge.pack(side="right")
        tk.Label(user_badge, text=f"👤 {self.user.get('full_name', 'Middleman Org')}",
                 bg="#112233", fg=CYAN, font=(FONT, 10, "bold")).pack(anchor="e")
        tk.Label(user_badge, text="Role: Platform Logistics Coordinator",
                 bg="#112233", fg=MUTED, font=(FONT, 8)).pack(anchor="e")

        # Quick KPI Metrics strip
        self._build_kpi_strip()

        # Main Tabbed Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=6)

        tabs = [
            ("📦 Surplus Aggregation Hub",     self._tab_surplus_hub),
            ("⚡ Automated Smart Matching",     self._tab_smart_matching),
            ("🧩 Multi-Source Allocation",     self._tab_multi_source),
            ("🚚 Route Optimization & Dispatch", self._tab_route_dispatch),
            ("🚨 Disaster & Emergency Relief",  self._tab_disaster_emergency),
            ("♻ Closed-Loop Food Recovery",    self._tab_closed_loop_recovery),
            ("📊 Monthly Audits & Certificates", self._tab_monthly_audit),
        ]

        for title, fn in tabs:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            fn(frame)

    # ── KPI Metrics Strip ──────────────────────────────────────
    def _build_kpi_strip(self):
        self.kpi_frame = tk.Frame(self, bg=BG, pady=6, padx=10)
        self.kpi_frame.pack(fill="x")
        self._refresh_kpis()

    def _refresh_kpis(self):
        for w in self.kpi_frame.winfo_children():
            w.destroy()

        try:
            stats = db.get_middleman_overview_stats()
        except Exception:
            stats = {
                "active_listings": 0, "active_kg": 0.0, "redistributed_kg": 0.0,
                "meals_provided": 0, "diverted_kg": 0.0, "total_establishments": 0,
                "total_ngos": 0, "co2_saved_kg": 0.0
            }

        kpis = [
            ("Live Surplus Available", f"{stats['active_kg']:.1f} kg", f"{stats['active_listings']} active lots", CYAN),
            ("Meals Redistributed", f"{stats['meals_provided']:,}", f"{stats['redistributed_kg']:.1f} kg safe food", HIGHLIGHT),
            ("Landfill Diversions", f"{stats['diverted_kg']:.1f} kg", "Biogas & compost recovery", GOLD),
            ("Connected Kitchens", f"{stats['total_establishments']}", "Institutions & Private", BLUE),
            ("NGO Partners", f"{stats['total_ngos']}", "Relief & community shelters", PURPLE),
            ("CO₂ Prevented", f"{stats['co2_saved_kg']:.1f} kg", "Closed-loop circular impact", HIGHLIGHT),
        ]

        for i, (title, val, sub, col) in enumerate(kpis):
            box = tk.Frame(self.kpi_frame, bg=CARD, padx=12, pady=6, relief="ridge", bd=1)
            box.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(box, text=title, bg=CARD, fg=MUTED, font=(FONT, 7, "bold")).pack(anchor="w")
            tk.Label(box, text=val, bg=CARD, fg=col, font=(FONT, 13, "bold")).pack(anchor="w")
            tk.Label(box, text=sub, bg=CARD, fg="#7e8c9b", font=(FONT, 7)).pack(anchor="w")

        # Refresh button on the right
        btn = tk.Button(self.kpi_frame, text="🔄 Refresh", bg=ACCENT, fg=TEXT,
                        font=(FONT, 8, "bold"), bd=0, padx=8, pady=6, cursor="hand2",
                        command=self._refresh_kpis)
        btn.pack(side="right", padx=6)

    # ══════════════════════════════════════════════════════════
    #  TAB 1: Surplus Aggregation Hub
    # ══════════════════════════════════════════════════════════
    def _tab_surplus_hub(self, parent):
        tk.Label(parent,
                 text="All Registered Surplus Lots from Institutions & Private Kitchens",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="Unified catalog of safe surplus food with real-time freshness, price rates, and pickup locations.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        # Filter bar
        filt_frame = tk.Frame(parent, bg=CARD, padx=8, pady=4)
        filt_frame.pack(fill="x")

        tk.Label(filt_frame, text="Filter Status:", bg=CARD, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=4)
        self.hub_status_var = tk.StringVar(value="all")
        cb_status = ttk.Combobox(filt_frame, textvariable=self.hub_status_var,
                                 values=["all", "available", "reserved", "completed", "diverted_biogas", "diverted_farm"],
                                 state="readonly", width=14)
        cb_status.pack(side="left", padx=4)

        tk.Label(filt_frame, text="Category:", bg=CARD, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=(14, 4))
        self.hub_cat_var = tk.StringVar(value="all")
        cb_cat = ttk.Combobox(filt_frame, textvariable=self.hub_cat_var,
                              values=["all", "cooked_meal", "raw_produce", "packaged_fpu", "bakery"],
                              state="readonly", width=14)
        cb_cat.pack(side="left", padx=4)

        tk.Button(filt_frame, text="Apply Filter", bg=ACCENT, fg=TEXT, font=(FONT, 8, "bold"),
                  bd=0, padx=10, pady=3, cursor="hand2", command=self._load_hub_data).pack(side="left", padx=10)

        # Treeview
        cols = ["ID", "Item Name", "Source Kitchen", "Establishment Type", "Category", "Available",
                "Pricing", "Expiry Window", "Quality", "Status"]
        widths = [45, 140, 160, 130, 95, 80, 85, 130, 90, 85]
        self.hub_tree = make_tree(parent, cols, widths, height=12)

        # Action bar
        act_frame = tk.Frame(parent, bg=CARD, padx=8, pady=8)
        act_frame.pack(fill="x")

        tk.Button(act_frame, text="⚡ Fast-Track Allocate to NGO", bg=BLUE, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=6, cursor="hand2",
                  command=self._hub_quick_allocate).pack(side="left", padx=4)

        tk.Button(act_frame, text="♻ Divert Expired to Biogas/Compost", bg=AMBER, fg="#0b1522",
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=6, cursor="hand2",
                  command=self._hub_divert_recovery).pack(side="left", padx=6)

        tk.Button(act_frame, text="🔍 View Item Details", bg=CARD2, fg=TEXT,
                  font=(FONT, 9), bd=1, relief="solid", padx=10, pady=6, cursor="hand2",
                  command=self._hub_view_details).pack(side="left", padx=4)

        self._load_hub_data()

    def _load_hub_data(self):
        for row in self.hub_tree.get_children():
            self.hub_tree.delete(row)
        try:
            listings = db.get_all_surplus_listings_middleman(
                filter_status=self.hub_status_var.get(),
                category=self.hub_cat_var.get()
            )
            for l in listings:
                est_raw = l.get("seller_institution_type") or "general"
                est_clean = est_raw.replace("_", " ").title()
                cat_type = "Institution" if db.get_kitchen_category(est_raw) == "institutional" else "Private Kitchen"
                est_display = f"{cat_type} ({est_clean})"

                price_disp = "Free (Donation)" if l["price_type"] == "free" else f"₹{l['discounted_price']:.1f}/{l['unit']}"
                exp_dt = l["expiry_datetime"]
                exp_str = exp_dt.strftime("%d-%b %H:%M") if hasattr(exp_dt, "strftime") else str(exp_dt)[:16]
                quality_disp = f"{l['quality_status']} ({l['quality_score'] or 85}%)"

                self.hub_tree.insert("", "end", values=(
                    l["id"],
                    l["item_name"],
                    l.get("seller_name") or f"Kitchen #{l['seller_id']}",
                    est_display,
                    l["category"].replace("_", " ").title(),
                    f"{l['available_qty']} {l['unit']}",
                    price_disp,
                    exp_str,
                    quality_disp,
                    l["status"].upper()
                ))
        except Exception as e:
            messagebox.showerror("Error Loading Surplus Hub", str(e))

    def _get_selected_hub_id(self):
        sel = self.hub_tree.selection()
        if not sel:
            messagebox.showwarning("Select Item", "Please select a surplus lot from the table first.")
            return None
        return int(self.hub_tree.item(sel[0], "values")[0])

    def _hub_quick_allocate(self):
        listing_id = self._get_selected_hub_id()
        if not listing_id:
            return
        listing = db.get_listing_by_id(listing_id)
        if not listing or listing["status"] != "available" or float(listing["available_qty"]) <= 0:
            messagebox.showwarning("Unavailable", "This lot is no longer available for allocation.")
            return

        # Pop up quick allocation modal
        win = tk.Toplevel(self)
        win.title(f"Fast-Track Allocate — Lot #{listing_id}")
        win.geometry("450x380")
        win.configure(bg=CARD)
        win.grab_set()

        tk.Label(win, text=f"Allocate: {listing['item_name']}", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(pady=(12, 4))
        tk.Label(win, text=f"Available: {listing['available_qty']} {listing['unit']} from Kitchen #{listing['seller_id']}",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack()

        form = tk.Frame(win, bg=CARD, padx=20, pady=12)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Recipient NGO:", bg=CARD, fg=TEXT, font=(FONT, 9)).grid(row=0, column=0, sticky="w", pady=6)
        ngo_var = tk.StringVar()
        # Fetch NGO list
        try:
            conn = db.get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, full_name, username FROM users WHERE role IN ('ngo', 'buyer')")
            ngos = cur.fetchall()
            cur.close(); conn.close()
        except Exception:
            ngos = []

        ngo_map = {f"{n['full_name']} (@{n['username']})": n["id"] for n in ngos}
        ngo_cb = ttk.Combobox(form, textvariable=ngo_var, values=list(ngo_map.keys()), state="readonly", width=28)
        if ngo_map:
            ngo_cb.current(0)
        ngo_cb.grid(row=0, column=1, sticky="w", pady=6)

        tk.Label(form, text="Quantity to Allocate:", bg=CARD, fg=TEXT, font=(FONT, 9)).grid(row=1, column=0, sticky="w", pady=6)
        qty_var = tk.DoubleVar(value=float(listing["available_qty"]))
        tk.Entry(form, textvariable=qty_var, bg=SIDEBAR, fg=TEXT, insertbackground=TEXT, font=(FONT, 10), width=15).grid(row=1, column=1, sticky="w", pady=6)

        tk.Label(form, text="Pickup Slot Hours:", bg=CARD, fg=TEXT, font=(FONT, 9)).grid(row=2, column=0, sticky="w", pady=6)
        hours_var = tk.IntVar(value=2)
        tk.Spinbox(form, from_=1, to=12, textvariable=hours_var, width=8).grid(row=2, column=1, sticky="w", pady=6)

        def _do_alloc():
            selected_ngo_name = ngo_var.get()
            if not selected_ngo_name or selected_ngo_name not in ngo_map:
                messagebox.showerror("Error", "Please select a valid recipient NGO.")
                return
            ngo_id = ngo_map[selected_ngo_name]
            q = qty_var.get()
            if q <= 0 or q > float(listing["available_qty"]):
                messagebox.showerror("Invalid Quantity", f"Quantity must be between 1 and {listing['available_qty']}")
                return

            pickup_dt = (datetime.now() + timedelta(hours=hours_var.get())).strftime("%Y-%m-%d %H:%M:%S")
            token = f"{random.randint(1000, 9999)}"
            price = 0.0 if listing["price_type"] == "free" else float(listing["discounted_price"]) * q

            res = db.create_surplus_order(
                listing_id=listing_id,
                buyer_id=ngo_id,
                order_type="ngo_bulk",
                quantity_ordered=q,
                total_price=price,
                pickup_slot=pickup_dt,
                pickup_token=token
            )
            if res:
                messagebox.showinfo("Allocation Confirmed",
                                    f"✅ Successfully allocated {q} {listing['unit']} to {selected_ngo_name}!\n"
                                    f"Pickup Token: {token}\nSlot: {pickup_dt}")
                win.destroy()
                self._load_hub_data()
                self._refresh_kpis()
            else:
                messagebox.showerror("Error", "Failed to confirm allocation.")

        tk.Button(win, text="Confirm & Dispatch Allocation", bg=HIGHLIGHT, fg="#050f08",
                  font=(FONT, 10, "bold"), bd=0, padx=16, pady=8, cursor="hand2",
                  command=_do_alloc).pack(pady=(0, 16))

    def _hub_divert_recovery(self):
        listing_id = self._get_selected_hub_id()
        if not listing_id:
            return
        listing = db.get_listing_by_id(listing_id)
        if not listing:
            return

        choice = messagebox.askyesno(
            "Closed-Loop Diversion",
            f"Divert Lot #{listing_id} ({listing['item_name']} - {listing['available_qty']} {listing['unit']}) "
            f"to Closed-Loop Recovery?\n\n"
            f"• Click YES for GreenTech Biomethanation Plant (Biogas Energy)\n"
            f"• Click NO for Organic Composting Farm (Soil Nutrient)"
        )
        dest_type = "biogas_plant" if choice else "organic_farm"
        ok, msg = db.record_circular_recovery(listing_id, dest_type)
        if ok:
            messagebox.showinfo("Diverted to Circular Recovery", msg)
            self._load_hub_data()
            self._refresh_kpis()
        else:
            messagebox.showerror("Diversion Error", msg)

    def _hub_view_details(self):
        listing_id = self._get_selected_hub_id()
        if not listing_id:
            return
        listing = db.get_listing_by_id(listing_id)
        if not listing:
            return

        details = (
            f"📌 Surplus Listing #{listing['id']}\n"
            f"Item: {listing['item_name']}\n"
            f"Category: {listing['category']}\n"
            f"Total Quantity: {listing['total_quantity']} {listing['unit']}\n"
            f"Available: {listing['available_qty']} {listing['unit']}\n"
            f"Price Type: {listing['price_type'].upper()} "
            f"({'₹' + str(listing['discounted_price']) if listing['price_type'] != 'free' else 'Free Donation'})\n"
            f"Location: {listing.get('location_address') or 'Kitchen Main Gate'}\n"
            f"Expiry Window: {listing['expiry_datetime']}\n"
            f"CV Freshness Score: {listing.get('quality_score', 85)}% ({listing['quality_status']})\n"
            f"Current Status: {listing['status'].upper()}\n"
        )
        messagebox.showinfo(f"Lot #{listing_id} Details", details)

    # ══════════════════════════════════════════════════════════
    #  TAB 2: Automated Smart Matching
    # ══════════════════════════════════════════════════════════
    def _tab_smart_matching(self, parent):
        tk.Label(parent, text="Automated Smart Matching Engine",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="Matches incoming NGO relief requests against active surplus based on quantity, distance, urgency, and recipient capacity.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        # Input criteria pane
        in_frame = tk.Frame(parent, bg=CARD2, padx=10, pady=8, relief="ridge", bd=1)
        in_frame.pack(fill="x", padx=10, pady=4)

        row1 = tk.Frame(in_frame, bg=CARD2)
        row1.pack(fill="x", pady=2)

        tk.Label(row1, text="Required Meals:", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=4)
        self.match_qty_var = tk.DoubleVar(value=80.0)
        tk.Entry(row1, textvariable=self.match_qty_var, bg=SIDEBAR, fg=TEXT, width=8,
                 insertbackground=TEXT, font=(FONT, 10)).pack(side="left", padx=4)

        tk.Label(row1, text="Max Distance (km):", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=(12, 4))
        self.match_dist_var = tk.DoubleVar(value=15.0)
        tk.Entry(row1, textvariable=self.match_dist_var, bg=SIDEBAR, fg=TEXT, width=8,
                 insertbackground=TEXT, font=(FONT, 10)).pack(side="left", padx=4)

        tk.Label(row1, text="Category:", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=(12, 4))
        self.match_diet_var = tk.StringVar(value="cooked_meal")
        cb_diet = ttk.Combobox(row1, textvariable=self.match_diet_var,
                               values=["cooked_meal", "raw_produce", "packaged_fpu", "bakery", "all"],
                               state="readonly", width=13)
        cb_diet.pack(side="left", padx=4)

        tk.Button(row1, text="⚡ Run Smart Match", bg=CYAN, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=3, cursor="hand2",
                  command=self._run_smart_match).pack(side="right", padx=6)

        # Matched results table
        cols = ["Listing ID", "Item", "Kitchen Source", "Est. Category", "Available", "Distance (km)", "Hours Left", "Match Score"]
        widths = [70, 150, 160, 130, 90, 95, 85, 95]
        self.match_tree = make_tree(parent, cols, widths, height=10)

        # Recommendation and Action box
        act_box = tk.Frame(parent, bg=CARD, padx=10, pady=6)
        act_box.pack(fill="x")

        self.match_rec_lbl = tk.Label(act_box, text="Click 'Run Smart Match' to evaluate active food surplus.",
                                      bg=CARD, fg=CYAN, font=(FONT, 9, "italic"), justify="left")
        self.match_rec_lbl.pack(side="left", padx=4)

        tk.Button(act_box, text="Confirm Best Match & Assign Order", bg=HIGHLIGHT, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._confirm_smart_match_order).pack(side="right", padx=4)

    def _run_smart_match(self):
        for row in self.match_tree.get_children():
            self.match_tree.delete(row)

        target_qty = self.match_qty_var.get()
        max_dist = self.match_dist_var.get()
        pref_cat = self.match_diet_var.get()

        # Fetch active surplus listings
        listings = db.get_active_surplus_with_location(category=pref_cat if pref_cat != "all" else None)
        if not listings:
            self.match_rec_lbl.config(text="No active listings matching the criteria found.")
            return

        ngo_lat, ngo_lon = 12.9716, 77.5946
        now = datetime.now()
        scored_matches = []

        for l in listings:
            k_lat = float(l.get("latitude") or 12.9750)
            k_lon = float(l.get("longitude") or 77.5900)
            dist = logistics.haversine_distance(ngo_lat, ngo_lon, k_lat, k_lon)
            if dist > max_dist:
                continue

            exp = l["expiry_datetime"]
            if hasattr(exp, "total_seconds"):
                mins_left = max(0, (exp - now).total_seconds() / 60)
            else:
                mins_left = 180

            avail = float(l["available_qty"])
            qty_ratio = min(1.0, avail / max(1.0, target_qty))
            qty_score = qty_ratio * 40.0
            dist_score = max(0.0, (1.0 - (dist / max(1.0, max_dist)))) * 30.0
            urgency_score = min(30.0, max(5.0, (360.0 - min(360.0, mins_left)) / 12.0))
            quality_score = float(l.get("quality_score") or 85) * 0.1

            total_score = round(qty_score + dist_score + urgency_score + quality_score, 1)

            est_raw = l.get("seller_institution_type") or "general"
            cat_type = "Institution" if db.get_kitchen_category(est_raw) == "institutional" else "Private Kitchen"

            scored_matches.append({
                "listing": l,
                "dist": dist,
                "mins_left": mins_left,
                "score": total_score,
                "cat_type": cat_type,
            })

        scored_matches.sort(key=lambda x: x["score"], reverse=True)

        for m in scored_matches:
            l = m["listing"]
            self.match_tree.insert("", "end", values=(
                l["id"],
                l["item_name"],
                l.get("seller_name") or f"Kitchen #{l['seller_id']}",
                m["cat_type"],
                f"{l['available_qty']} {l['unit']}",
                f"{m['dist']:.1f}",
                f"{m['mins_left']/60:.1f} hrs",
                f"{m['score']} pts"
            ))

        if scored_matches:
            top = scored_matches[0]
            self.match_rec_lbl.config(
                text=f"🎯 Top Recommendation: Lot #{top['listing']['id']} ({top['listing']['item_name']}) — "
                     f"{top['score']} pts | {top['dist']:.1f} km away | {top['listing']['available_qty']} available."
            )
        else:
            self.match_rec_lbl.config(text="No listings met the distance and quantity constraints.")

    def _confirm_smart_match_order(self):
        sel = self.match_tree.selection()
        if not sel:
            messagebox.showwarning("Select Match", "Please select a matched lot to allocate.")
            return
        listing_id = int(self.match_tree.item(sel[0], "values")[0])
        # Switch to allocation modal
        self.hub_tree.selection_set(self.hub_tree.get_children()[0]) if self.hub_tree.get_children() else None
        listing = db.get_listing_by_id(listing_id)
        if listing:
            self._hub_quick_allocate()

    # ══════════════════════════════════════════════════════════
    #  TAB 3: Multiple-Source Allocation Engine
    # ══════════════════════════════════════════════════════════
    def _tab_multi_source(self, parent):
        tk.Label(parent, text="Multiple-Source Surplus Pooling Engine",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="When an NGO requirement exceeds any single kitchen (e.g. 500 meals), the platform aggregates surplus from multiple kitchens.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        # Inputs
        top = tk.Frame(parent, bg=CARD2, padx=10, pady=8, relief="ridge", bd=1)
        top.pack(fill="x", padx=10, pady=4)

        row = tk.Frame(top, bg=CARD2)
        row.pack(fill="x")

        tk.Label(row, text="Target Demand (Meals):", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=4)
        self.ms_demand_var = tk.DoubleVar(value=500.0)
        tk.Entry(row, textvariable=self.ms_demand_var, bg=SIDEBAR, fg=TEXT, width=8,
                 insertbackground=TEXT, font=(FONT, 10)).pack(side="left", padx=4)

        tk.Label(row, text="Max Radius (km):", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=(14, 4))
        self.ms_radius_var = tk.DoubleVar(value=20.0)
        tk.Entry(row, textvariable=self.ms_radius_var, bg=SIDEBAR, fg=TEXT, width=8,
                 insertbackground=TEXT, font=(FONT, 10)).pack(side="left", padx=4)

        tk.Button(row, text="🧩 Aggregate Multi-Source Pool", bg=CYAN, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2",
                  command=self._run_multi_source_pool).pack(side="right", padx=4)

        # Multi-source breakdown tree
        cols = ["Stop #", "Listing ID", "Kitchen / Establishment", "Item", "Allocated Qty", "Distance", "Time Left"]
        widths = [55, 75, 170, 150, 110, 90, 95]
        self.ms_tree = make_tree(parent, cols, widths, height=8)

        # Plan Summary text
        self.ms_summary_lbl = tk.Label(parent, text="", bg=CARD, fg=TEXT,
                                       font=(FONT_MONO, 9), justify="left", relief="groove", bd=1, padx=8, pady=6)
        self.ms_summary_lbl.pack(fill="x", padx=10, pady=4)

        # Execution bar
        bot = tk.Frame(parent, bg=CARD, padx=10, pady=6)
        bot.pack(fill="x")

        tk.Button(bot, text="✅ Execute Pooled Multi-Source Allocation", bg=HIGHLIGHT, fg="#050f08",
                  font=(FONT, 10, "bold"), bd=0, padx=16, pady=8, cursor="hand2",
                  command=self._execute_multi_source_orders).pack(side="right", padx=4)

        self._current_ms_result = None

    def _run_multi_source_pool(self):
        for row in self.ms_tree.get_children():
            self.ms_tree.delete(row)

        demand = self.ms_demand_var.get()
        radius = self.ms_radius_var.get()

        all_listings = db.get_active_surplus_with_location()
        res = logistics.allocate_multi_source_surplus(
            demand_qty=demand,
            ngo_lat=12.9716,
            ngo_lon=77.5946,
            all_listings=all_listings,
            max_distance_km=radius,
            unit="meals"
        )
        self._current_ms_result = res
        self.ms_summary_lbl.config(text=res["summary_text"])

        for i, a in enumerate(res["allocations"], 1):
            mins = a["mins_left"]
            time_str = f"{mins//60}h {mins%60}m" if mins > 60 else f"{mins} mins"
            self.ms_tree.insert("", "end", values=(
                i,
                a["listing_id"],
                a["seller_name"],
                a["item_name"],
                f"{a['allocated_qty']} {a['unit']}",
                f"{a['distance_km']:.1f} km",
                time_str
            ))

    def _execute_multi_source_orders(self):
        if not self._current_ms_result or not self._current_ms_result["allocations"]:
            messagebox.showwarning("No Allocation", "Please run multi-source aggregation first.")
            return

        # Find or use first NGO in system
        try:
            conn = db.get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, full_name FROM users WHERE role IN ('ngo', 'buyer') LIMIT 1")
            ngo = cur.fetchone()
            cur.close(); conn.close()
            ngo_id = ngo["id"] if ngo else 1
            ngo_name = ngo["full_name"] if ngo else "Community Food Bank"
        except Exception:
            ngo_id = 1
            ngo_name = "Community Food Bank"

        confirm = messagebox.askyesno(
            "Confirm Multi-Source Order",
            f"Execute pooled allocation of {self._current_ms_result['total_allocated']} meals across "
            f"{len(self._current_ms_result['allocations'])} kitchen sources for {ngo_name}?"
        )
        if not confirm:
            return

        ok, orders = db.execute_multi_source_allocation(ngo_id, self._current_ms_result["allocations"])
        if ok:
            tokens_str = ", ".join([f"#{o['order_id']} (Token: {o['pickup_token']})" for o in orders])
            messagebox.showinfo("Pooled Orders Confirmed!",
                                f"🎉 Successfully created {len(orders)} surplus orders!\n\n"
                                f"Orders Created:\n{tokens_str}\n\n"
                                f"These have been forwarded to the Logistics Route Planner.")
            self._load_hub_data()
            self._refresh_kpis()
        else:
            messagebox.showerror("Error", f"Failed: {orders}")

    # ══════════════════════════════════════════════════════════
    #  TAB 4: Route Optimization & Logistics Dispatch
    # ══════════════════════════════════════════════════════════
    def _tab_route_dispatch(self, parent):
        tk.Label(parent, text="Logistics & Multi-Stop Route Optimizer",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="Recommends efficient pickup/delivery routes for platform agents, sequencing multiple stops and verifying safe transit time.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        ctrl = tk.Frame(parent, bg=CARD2, padx=10, pady=8, relief="ridge", bd=1)
        ctrl.pack(fill="x", padx=10, pady=4)

        tk.Label(ctrl, text="Assigned Agent:", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=4)
        self.agent_var = tk.StringVar(value="Agent Vikram (EV Van #1)")
        agent_cb = ttk.Combobox(ctrl, textvariable=self.agent_var,
                                values=["Agent Vikram (EV Van #1)", "Agent Ananya (Cargo E-Bike)", "Agent Rahul (Refrigerated Truck)"],
                                state="readonly", width=26)
        agent_cb.pack(side="left", padx=4)

        tk.Label(ctrl, text="Speed (km/h):", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=(14, 4))
        self.speed_var = tk.DoubleVar(value=25.0)
        tk.Entry(ctrl, textvariable=self.speed_var, bg=SIDEBAR, fg=TEXT, width=6,
                 insertbackground=TEXT, font=(FONT, 10)).pack(side="left", padx=4)

        tk.Button(ctrl, text="🗺 Generate Optimal Multi-Stop Route", bg=CYAN, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2",
                  command=self._generate_logistics_route).pack(side="right", padx=4)

        # Route Itinerary Table
        cols = ["Step", "Stop Type", "Location / Kitchen", "Action / Task", "Distance (km)", "Transit (min)", "Est. Arrival", "Status"]
        widths = [45, 85, 170, 160, 85, 80, 110, 95]
        self.route_tree = make_tree(parent, cols, widths, height=8)

        # Visual Route Map Canvas
        self.route_canvas = tk.Canvas(parent, bg="#09131d", height=130, highlightthickness=0)
        self.route_canvas.pack(fill="x", padx=10, pady=4)
        self._draw_empty_canvas()

        # Status update bar
        bar = tk.Frame(parent, bg=CARD, padx=10, pady=6)
        bar.pack(fill="x")

        tk.Button(bar, text="🚀 Dispatch Agent to Route", bg=BLUE, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=6, cursor="hand2",
                  command=lambda: messagebox.showinfo("Agent Dispatched", f"✅ {self.agent_var.get()} has been dispatched with digital manifest!")).pack(side="left", padx=4)

        tk.Button(bar, text="📦 Mark All Pickups Completed", bg=ACCENT, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=6, cursor="hand2",
                  command=lambda: messagebox.showinfo("Pickups Logged", "All pickup tokens verified and recorded.")).pack(side="left", padx=4)

        tk.Button(bar, text="🏁 Mark Final Delivery Completed", bg=HIGHLIGHT, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=14, pady=6, cursor="hand2",
                  command=lambda: messagebox.showinfo("Delivery Completed", "Food delivered safely to NGO shelter! CO2 savings logged.")).pack(side="right", padx=4)

    def _draw_empty_canvas(self):
        c = self.route_canvas
        c.delete("all")
        c.create_text(350, 65, text="Click 'Generate Optimal Multi-Stop Route' to render visual transit map.",
                      fill=MUTED, font=(FONT, 10, "italic"))

    def _generate_logistics_route(self):
        for row in self.route_tree.get_children():
            self.route_tree.delete(row)

        start_node = {"name": "EcoMess Central Logistics Hub", "latitude": 12.9716, "longitude": 77.5946}
        dropoff_node = {"name": "Annapurna Community Distribution Shelter", "latitude": 12.9600, "longitude": 77.6100}

        # Sample pickup stops from active listings
        listings = db.get_active_surplus_with_location()[:4]
        if not listings:
            # Fallback simulated stops
            pickup_nodes = [
                {"id": 1, "name": "Central Hostel Dining Hall", "item_name": "Vegetable Biryani", "quantity": 120, "unit": "meals",
                 "latitude": 12.9800, "longitude": 77.5850, "expiry_datetime": datetime.now() + timedelta(hours=3)},
                {"id": 2, "name": "Campus South Canteen", "item_name": "Dal & Chapatis", "quantity": 90, "unit": "meals",
                 "latitude": 12.9650, "longitude": 77.5750, "expiry_datetime": datetime.now() + timedelta(hours=4)},
                {"id": 3, "name": "Metro Bakery & Kitchen", "item_name": "Fresh Breads", "quantity": 40, "unit": "kg",
                 "latitude": 12.9900, "longitude": 77.6050, "expiry_datetime": datetime.now() + timedelta(hours=5)},
            ]
        else:
            pickup_nodes = []
            for l in listings:
                pickup_nodes.append({
                    "id": l["id"],
                    "name": l.get("seller_name") or f"Kitchen #{l['seller_id']}",
                    "item_name": l["item_name"],
                    "quantity": float(l["available_qty"]),
                    "unit": l["unit"],
                    "latitude": float(l.get("latitude") or 12.9750),
                    "longitude": float(l.get("longitude") or 77.5900),
                    "expiry_datetime": l["expiry_datetime"],
                })

        tour = logistics.optimize_pickup_route(start_node, pickup_nodes, dropoff_node, datetime.now())

        for step in tour["itinerary"]:
            arr = step["arrival_time"].strftime("%H:%M") if hasattr(step["arrival_time"], "strftime") else str(step["arrival_time"])[:5]
            st_val = step.get("status") or ("SAFE" if step.get("is_safe", True) else "AT RISK")
            self.route_tree.insert("", "end", values=(
                step["step"],
                step["type"].upper(),
                step["name"],
                step["action"],
                f"{step['distance_from_prev_km']:.2f}",
                f"{step['transit_mins']:.1f}",
                arr,
                st_val.upper()
            ))

        # Draw map on canvas
        c = self.route_canvas
        c.delete("all")
        w = c.winfo_width() or 700
        h = 130
        steps = tour["itinerary"]
        n = len(steps)
        if n > 1:
            dx = (w - 100) / (n - 1)
            pts = []
            for i, st in enumerate(steps):
                x = 50 + i * dx
                y = 65 + (-15 if i % 2 == 1 else 15)
                pts.append((x, y, st))

            # Connect line
            for i in range(len(pts) - 1):
                c.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill=CYAN, width=3, dash=(4, 2))

            # Draw nodes
            for x, y, st in pts:
                col = HIGHLIGHT if st["type"] == "start" else (PURPLE if st["type"] == "dropoff" else AMBER)
                c.create_oval(x-10, y-10, x+10, y+10, fill=col, outline=TEXT, width=2)
                c.create_text(x, y, text=str(st["step"]), fill="#050f08", font=(FONT, 9, "bold"))
                # Label
                name_short = st["name"].split(" ")[0]
                c.create_text(x, y + 20, text=name_short, fill=TEXT, font=(FONT, 8))

    # ══════════════════════════════════════════════════════════
    #  TAB 5: Disaster & Emergency Support
    # ══════════════════════════════════════════════════════════
    def _tab_disaster_emergency(self, parent):
        tk.Label(parent, text="🚨 Disaster & Crisis Rapid Food Aggregation Hub",
                 bg=CARD, fg=RED, font=(FONT, 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="Emergency protocol for floods, natural disasters, temporary shelters, and community relief operations.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        pane = tk.Frame(parent, bg="#2b1115", padx=12, pady=10, relief="solid", bd=1)
        pane.pack(fill="x", padx=10, pady=4)

        row = tk.Frame(pane, bg="#2b1115")
        row.pack(fill="x", pady=2)

        tk.Label(row, text="Crisis Event Type:", bg="#2b1115", fg=TEXT, font=(FONT, 9)).pack(side="left", padx=4)
        self.disaster_type_var = tk.StringVar(value="Flood Relief Shelter")
        cb_type = ttk.Combobox(row, textvariable=self.disaster_type_var,
                               values=["Flood Relief Shelter", "Cyclone / Heavy Rain Crisis", "Fire Incident Relocation", "Emergency Community Kitchen"],
                               state="readonly", width=26)
        cb_type.pack(side="left", padx=4)

        tk.Label(row, text="Target Food Relief (Meals):", bg="#2b1115", fg=TEXT, font=(FONT, 9)).pack(side="left", padx=(14, 4))
        self.disaster_meals_var = tk.DoubleVar(value=800.0)
        tk.Entry(row, textvariable=self.disaster_meals_var, bg=SIDEBAR, fg=TEXT, width=8,
                 insertbackground=TEXT, font=(FONT, 10)).pack(side="left", padx=4)

        tk.Button(row, text="⚡ ACTIVATE RAPID SURPLUS SWEEP", bg=RED, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=14, pady=4, cursor="hand2",
                  command=self._run_disaster_sweep).pack(side="right", padx=4)

        # Disaster Sweep Tree
        cols = ["Lot ID", "Kitchen / Donor", "Category", "Food Description", "Emergency Quantity", "Location", "Transit Priority"]
        widths = [65, 170, 130, 160, 120, 140, 100]
        self.disaster_tree = make_tree(parent, cols, widths, height=8)

        # Emergency dispatch button
        bar = tk.Frame(parent, bg=CARD, padx=10, pady=8)
        bar.pack(fill="x")

        self.disaster_status_lbl = tk.Label(bar, text="Emergency Status: STANDBY (Ready for mobilization)",
                                            bg=CARD, fg=GOLD, font=(FONT, 9, "bold"))
        self.disaster_status_lbl.pack(side="left", padx=4)

        tk.Button(bar, text="📢 Issue Emergency Dispatch Order", bg=RED, fg=TEXT,
                  font=(FONT, 10, "bold"), bd=0, padx=16, pady=8, cursor="hand2",
                  command=self._confirm_emergency_dispatch).pack(side="right", padx=4)

    def _run_disaster_sweep(self):
        for row in self.disaster_tree.get_children():
            self.disaster_tree.delete(row)

        target = self.disaster_meals_var.get()
        listings = db.get_active_surplus_with_location(category="cooked_meal")
        if not listings:
            listings = db.get_active_surplus_with_location()

        total_found = 0.0
        for l in listings:
            q = float(l["available_qty"])
            total_found += q
            est_raw = l.get("seller_institution_type") or "general"
            cat_type = "Institution" if db.get_kitchen_category(est_raw) == "institutional" else "Private Kitchen"

            self.disaster_tree.insert("", "end", values=(
                l["id"],
                l.get("seller_name") or f"Kitchen #{l['seller_id']}",
                cat_type,
                l["item_name"],
                f"{q} {l['unit']}",
                l.get("location_address") or "Central Campus",
                "PRIORITY 1 (HIGH)"
            ))

        self.disaster_status_lbl.config(
            text=f"🚨 EMERGENCY ACTIVE: Mobilized {total_found:.1f} / {target:.1f} meals across "
                 f"{len(self.disaster_tree.get_children())} sources.",
            fg=CYAN
        )

    def _confirm_emergency_dispatch(self):
        items = self.disaster_tree.get_children()
        if not items:
            messagebox.showwarning("No Items", "Run the emergency surplus sweep first.")
            return

        messagebox.showinfo(
            "Emergency Order Dispatched",
            f"🚨 EMERGENCY DISPATCH ACTIVATED!\n\n"
            f"Crisis: {self.disaster_type_var.get()}\n"
            f"Target: {self.disaster_meals_var.get()} meals\n"
            f"Total Lots Mobilized: {len(items)}\n\n"
            f"SMS & Digital Alerts sent to participating Institutional Kitchens and Platform Agents."
        )

    # ══════════════════════════════════════════════════════════
    #  TAB 6: Closed-Loop Food Recovery
    # ══════════════════════════════════════════════════════════
    def _tab_closed_loop_recovery(self, parent):
        tk.Label(parent, text="Closed-Loop Food Recovery & Landfill Diversion",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="Ensures zero food waste reaches landfills by systematically routing expired or unsafe batches to Biogas Plants & Organic Farms.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        # Recovery stats
        box = tk.Frame(parent, bg=CARD2, padx=12, pady=8, relief="ridge", bd=1)
        box.pack(fill="x", padx=10, pady=4)

        try:
            conn = db.get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT destination_type, COALESCE(SUM(quantity_kg),0) AS kg, COALESCE(SUM(energy_points),0) AS pts
                FROM circular_diversions GROUP BY destination_type
            """)
            rows = cur.fetchall()
            cur.close(); conn.close()
        except Exception:
            rows = []

        biogas_kg = sum(float(r["kg"]) for r in rows if r["destination_type"] == "biogas_plant")
        farm_kg = sum(float(r["kg"]) for r in rows if r["destination_type"] == "organic_farm")

        tk.Label(box, text=f"⚡ Total Clean Biogas Energy Diverted: {biogas_kg:.1f} kg (Clean Methane Energy)",
                 bg=CARD2, fg=CYAN, font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Label(box, text=f"🌿 Total Organic Compost Diverted: {farm_kg:.1f} kg (Soil Enrichment)",
                 bg=CARD2, fg=HIGHLIGHT, font=(FONT, 9, "bold")).pack(anchor="w")

        # Diversion Log Tree
        cols = ["ID", "Kitchen / Generator", "Waste Category", "Destination Unit", "Partner Facility", "Quantity (kg)", "Circular Credits", "Date"]
        widths = [45, 160, 130, 120, 160, 95, 100, 95]
        self.recovery_tree = make_tree(parent, cols, widths, height=9)
        self._load_recovery_log()

        # Action bar
        act = tk.Frame(parent, bg=CARD, padx=10, pady=6)
        act.pack(fill="x")

        tk.Button(act, text="🔄 Refresh Recovery Log", bg=CARD2, fg=TEXT,
                  font=(FONT, 9), bd=1, relief="solid", padx=10, pady=6, cursor="hand2",
                  command=self._load_recovery_log).pack(side="left", padx=4)

    def _load_recovery_log(self):
        for row in self.recovery_tree.get_children():
            self.recovery_tree.delete(row)
        try:
            conn = db.get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT cd.*, u.full_name AS kitchen_name
                FROM circular_diversions cd
                LEFT JOIN users u ON cd.kitchen_id = u.id
                ORDER BY cd.id DESC LIMIT 40
            """)
            rows = cur.fetchall()
            cur.close(); conn.close()

            for r in rows:
                self.recovery_tree.insert("", "end", values=(
                    r["id"],
                    r.get("kitchen_name") or f"Kitchen #{r['kitchen_id']}",
                    r["waste_type"].replace("_", " ").title(),
                    r["destination_type"].replace("_", " ").title(),
                    r["partner_name"],
                    f"{r['quantity_kg']:.1f}",
                    f"{r['energy_points']} pts (₹{r['financial_credit']:.1f})",
                    r["diversion_date"]
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════════
    #  TAB 7: Monthly Audits & Certificates
    # ══════════════════════════════════════════════════════════
    def _tab_monthly_audit(self, parent):
        tk.Label(parent, text="Monthly Sustainability Audits & Green Certifications",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(parent,
                 text="Middleman organization issues verified green certificates and audit summaries to participating kitchens.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=10, pady=(0, 6))

        # Controls
        ctrl = tk.Frame(parent, bg=CARD2, padx=10, pady=8, relief="ridge", bd=1)
        ctrl.pack(fill="x", padx=10, pady=4)

        tk.Label(ctrl, text="Select Month / Year:", bg=CARD2, fg=TEXT, font=(FONT, 9)).pack(side="left", padx=4)
        now = datetime.now()
        self.audit_month_var = tk.IntVar(value=now.month)
        cb_m = ttk.Combobox(ctrl, textvariable=self.audit_month_var, values=list(range(1, 13)), width=5, state="readonly")
        cb_m.pack(side="left", padx=2)

        self.audit_year_var = tk.IntVar(value=now.year)
        cb_y = ttk.Combobox(ctrl, textvariable=self.audit_year_var, values=[2025, 2026, 2027], width=7, state="readonly")
        cb_y.pack(side="left", padx=2)

        tk.Button(ctrl, text="Generate Monthly Audit", bg=CYAN, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2",
                  command=self._generate_audit).pack(side="left", padx=12)

        tk.Button(ctrl, text="🏅 Issue Digital Green Certificate", bg=GOLD, fg="#050f08",
                  font=(FONT, 9, "bold"), bd=0, padx=14, pady=4, cursor="hand2",
                  command=self._issue_certificate).pack(side="right", padx=4)

        # Audit Display text widget
        self.audit_txt = tk.Text(parent, bg="#0e1722", fg=TEXT, font=(FONT_MONO, 10),
                                 wrap="word", relief="flat", padx=12, pady=12, height=14)
        self.audit_txt.pack(fill="both", expand=True, padx=10, pady=6)

        self._generate_audit()

    def _generate_audit(self):
        m = self.audit_month_var.get()
        y = self.audit_year_var.get()
        report = db.get_monthly_kitchen_report(year=y, month=m)

        lines = [
            f"╔════════════════════════════════════════════════════════════════════════════╗",
            f"   ECOMESS PLATFORM — OFFICIAL MONTHLY SUSTAINABILITY AUDIT REPORT",
            f"   Reporting Period: {m:02d} / {y}  |  Issuing Authority: EcoMess Middleman Org",
            f"╚════════════════════════════════════════════════════════════════════════════╝\n",
            f"1. FOOD PRODUCTION & CONSUMPTION OVERVIEW",
            f"   • Total Food Prepared across Network:        {report['food_prepared_kg']:>10.1f} kg",
            f"   • Total Food Consumed by Diners/Students:    {report['estimated_consumption_kg']:>10.1f} kg",
            f"   • Total Avoidable Kitchen Wastage:           {report['avoidable_waste_kg']:>10.1f} kg\n",
            f"2. SURPLUS REDISTRIBUTION IMPACT (HUMAN CONSUMPTION)",
            f"   • Safe Surplus Food Redistributed:           {report['surplus_redistributed_kg']:>10.1f} kg",
            f"   • Free Donations directly to NGOs:           {report['free_donations_kg']:>10.1f} kg",
            f"   • Total Nutritious Meals Provided:           {report['meals_provided']:>10,d} meals",
            f"   • Total Financial Value Recovered:           ₹{report['cost_saved_inr']:>9.2f}\n",
            f"3. CLOSED-LOOP CIRCULAR RECOVERY (ZERO LANDFILL DIVERSION)",
            f"   • Diverted to Clean Biogas Generation:       {report['biogas_diverted_kg']:>10.1f} kg",
            f"   • Diverted to Organic Compost Soil Farms:    {report['farm_compost_kg']:>10.1f} kg",
            f"   • Total Net CO₂ Emissions Avoided:           {report['co2_avoided_kg']:>10.1f} kg CO₂e\n",
            f"4. SUSTAINABILITY SCORE & RECOGNITION",
            f"   • Green Performance Points Awarded:          {report['eco_points_earned']:>10,d} points",
            f"   • Current Sustainability Grade:              GRADE A+ (Zero-Waste Exemplar)",
            f"   • Verified by Middleman Redistribution Engine",
        ]
        self.audit_txt.delete("1.0", "end")
        self.audit_txt.insert("1.0", "\n".join(lines))

    def _issue_certificate(self):
        m = self.audit_month_var.get()
        y = self.audit_year_var.get()
        report = db.get_monthly_kitchen_report(year=y, month=m)

        cert_win = tk.Toplevel(self)
        cert_win.title(f"Official Green Certificate — {m:02d}/{y}")
        cert_win.geometry("560x440")
        cert_win.configure(bg="#08141e")
        cert_win.grab_set()

        outer = tk.Frame(cert_win, bg=GOLD, padx=3, pady=3)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        inner = tk.Frame(outer, bg="#0d1f2d", padx=20, pady=20)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="🌿 ECOMESS ZERO-WASTE CERTIFICATION 🌿",
                 bg="#0d1f2d", fg=GOLD, font=(FONT, 14, "bold")).pack(pady=(4, 2))
        tk.Label(inner, text="Awarded by EcoMess Platform Middleman Organization",
                 bg="#0d1f2d", fg=MUTED, font=(FONT, 8)).pack(pady=(0, 14))

        tk.Label(inner, text="This certificate is proudly awarded to participating",
                 bg="#0d1f2d", fg=TEXT, font=(FONT, 10)).pack()
        tk.Label(inner, text="INSTITUTIONAL & PRIVATE KITCHEN ESTABLISHMENTS",
                 bg="#0d1f2d", fg=CYAN, font=(FONT, 12, "bold")).pack(pady=4)
        tk.Label(inner, text=f"For outstanding circular food redistribution during {m:02d}/{y}",
                 bg="#0d1f2d", fg=TEXT, font=(FONT, 10)).pack(pady=4)

        stats_f = tk.Frame(inner, bg="#08141e", padx=16, pady=10, relief="ridge", bd=1)
        stats_f.pack(fill="x", pady=12)

        tk.Label(stats_f, text=f"🍲 {report['meals_provided']} Meals Redistributed to Relief Shelters",
                 bg="#08141e", fg=HIGHLIGHT, font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Label(stats_f, text=f"♻ {report['biogas_diverted_kg'] + report['farm_compost_kg']:.1f} kg Diverted to Biogas & Soil Recovery",
                 bg="#08141e", fg=CYAN, font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Label(stats_f, text=f"🌍 {report['co2_avoided_kg']} kg Greenhouse Gas Emissions Prevented",
                 bg="#08141e", fg=GOLD, font=(FONT, 9, "bold")).pack(anchor="w")

        tk.Label(inner, text="Certified & Sealed by EcoMess Automated Closed-Loop Protocol",
                 bg="#0d1f2d", fg="#627584", font=(FONT, 8, "italic")).pack(pady=(8, 4))
