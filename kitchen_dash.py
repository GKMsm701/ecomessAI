"""
kitchen_dash.py — EcoMESS AI Kitchen & Food Processing Unit (FPU) Dashboard
Enables kitchen managers and FPUs to post surplus food, run simulated CV freshness scans,
manage NGO/buyer pickups, route waste to biogas/farms, and track sustainability rewards.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
import random

import database as db

# ── Color Palette (Consistent Dark Eco-Green) ─────────────────
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
#  Kitchen & FPU Dashboard
# ══════════════════════════════════════════════════════════════
class KitchenDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.user = app.current_user
        self.configure(style="TFrame")
        self._cv_scan_done = False
        self._cv_score = 5
        self._build()

    def _build(self):
        # Header banner
        header = tk.Frame(self, bg="#1b4332", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        name = self.user.get('full_name') or self.user['username']
        tk.Label(header, text=f"🍲 Kitchen & FPU Operations — {name}",
                 bg="#1b4332", fg=TEXT, font=(FONT, 13, "bold")).pack(side="left", padx=20)

        pts = db.get_user_points(self.user["id"])
        self.pts_lbl = tk.Label(header, text=f"⭐ Eco-Points: {pts} pts",
                                bg="#0d2818", fg=GOLD, font=(FONT, 11, "bold"),
                                padx=12, pady=4)
        self.pts_lbl.pack(side="right", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = [
            ("Post Surplus & CV Inspect", self._tab_post_surplus),
            ("Active Listings & Orders",  self._tab_listings_orders),
            ("Circular Waste Diversion",  self._tab_circular_diversion),
            ("Rewards & Impact Ledger",   self._tab_rewards_ledger),
            ("User Manual",               self._tab_manual),
        ]
        for label, builder in tabs:
            frame = tk.Frame(notebook, bg=CARD)
            notebook.add(frame, text=f"  {label}  ")
            builder(frame)

    def _refresh_points_banner(self):
        pts = db.get_user_points(self.user["id"])
        self.pts_lbl.config(text=f"⭐ Eco-Points: {pts} pts")

    # ── TAB 1: Post Surplus & CV Inspect ─────────────────────────
    def _tab_post_surplus(self, parent):
        tk.Label(parent, text="List Surplus Food / Near-Expiry Stock",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(parent, text="Institutional kitchens & FPUs can offer surplus food for free to NGOs or at subsidized rates to local buyers.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=14, pady=(0, 10))

        # Main horizontal container
        container = tk.Frame(parent, bg=CARD)
        container.pack(fill="both", expand=True, padx=12, pady=4)

        # Left Form Frame
        form_frame = tk.LabelFrame(container, text=" Listing Details ", bg=CARD, fg=HIGHLIGHT,
                                   font=(FONT, 10, "bold"), padx=12, pady=10)
        form_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        def add_row(parent, label_text, var, width=22):
            row = tk.Frame(parent, bg=CARD)
            row.pack(fill="x", pady=4)
            lbl(row, label_text, width=16, anchor="w").pack(side="left")
            e = ent(row, var, width=width)
            e.pack(side="left")
            return e

        self.item_name = tk.StringVar(value="Vegetable Pulao & Dal")
        add_row(form_frame, "Food Item Name:", self.item_name, 26)

        row_cat = tk.Frame(form_frame, bg=CARD)
        row_cat.pack(fill="x", pady=4)
        lbl(row_cat, "Category:", width=16, anchor="w").pack(side="left")
        self.cat_var = tk.StringVar(value="cooked_meal")
        cat_cb = ttk.Combobox(row_cat, textvariable=self.cat_var,
                              values=["cooked_meal", "raw_produce", "packaged_fpu", "bakery"],
                              state="readonly", width=20)
        cat_cb.pack(side="left")

        row_qty = tk.Frame(form_frame, bg=CARD)
        row_qty.pack(fill="x", pady=4)
        lbl(row_qty, "Quantity & Unit:", width=16, anchor="w").pack(side="left")
        self.qty_var = tk.StringVar(value="35.0")
        ent(row_qty, self.qty_var, 10).pack(side="left", padx=(0, 6))
        self.unit_var = tk.StringVar(value="kg")
        ttk.Combobox(row_qty, textvariable=self.unit_var, values=["kg", "servings", "packets", "boxes"],
                     state="readonly", width=8).pack(side="left")

        row_exp = tk.Frame(form_frame, bg=CARD)
        row_exp.pack(fill="x", pady=4)
        lbl(row_exp, "Safe for (Hours):", width=16, anchor="w").pack(side="left")
        self.exp_hours = tk.StringVar(value="4")
        ttk.Combobox(row_exp, textvariable=self.exp_hours, values=["2", "4", "6", "12", "24", "48"],
                     state="readonly", width=10).pack(side="left")
        lbl(row_exp, "from now", fg=MUTED).pack(side="left", padx=6)

        row_price = tk.Frame(form_frame, bg=CARD)
        row_price.pack(fill="x", pady=4)
        lbl(row_price, "Price Model:", width=16, anchor="w").pack(side="left")
        self.price_type = tk.StringVar(value="free")
        tk.Radiobutton(row_price, text="Free (for NGOs/Shelters)", variable=self.price_type,
                       value="free", bg=CARD, fg=HIGHLIGHT, selectcolor=SIDEBAR,
                       command=self._on_price_type_change).pack(side="left", padx=(0, 8))
        tk.Radiobutton(row_price, text="Discounted Rate", variable=self.price_type,
                       value="discounted", bg=CARD, fg=TEXT, selectcolor=SIDEBAR,
                       command=self._on_price_type_change).pack(side="left")

        self.row_disc = tk.Frame(form_frame, bg=CARD)
        lbl(self.row_disc, "Discounted Rate (₹):", width=16, anchor="w").pack(side="left")
        self.disc_rate = tk.StringVar(value="20.0")
        ent(self.row_disc, self.disc_rate, 10).pack(side="left")
        lbl(self.row_disc, "per unit", fg=MUTED).pack(side="left", padx=6)

        self.loc_var = tk.StringVar(value="Hostel Block A Central Kitchen, Campus Road")
        add_row(form_frame, "Pickup Location:", self.loc_var, 30)

        # Right Frame: CV Quality Inspector
        cv_frame = tk.LabelFrame(container, text=" AI / Computer Vision Freshness Scan ", bg=CARD, fg=HIGHLIGHT,
                                 font=(FONT, 10, "bold"), padx=14, pady=10)
        cv_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        tk.Label(cv_frame,
                 text="Prior to redistribution, institutional food must pass computer vision quality validation.\n"
                      "The scanner checks visual texture, color discolouration, and steam freshness markers.",
                 bg=CARD, fg=MUTED, font=(FONT, 8), justify="left").pack(anchor="w", pady=(0, 10))

        # Preview card for CV scanner
        self.cv_preview = tk.Frame(cv_frame, bg="#0d1b2a", relief="solid", bd=1, height=140)
        self.cv_preview.pack(fill="x", pady=8)
        self.cv_preview.pack_propagate(False)

        self.cv_status_lbl = tk.Label(self.cv_preview, text="📷 No image scanned yet.\nClick 'Run CV Inspection' below.",
                                      bg="#0d1b2a", fg=MUTED, font=(FONT, 10))
        self.cv_status_lbl.pack(expand=True)

        self.cv_badge = tk.Label(cv_frame, text="⏳ Quality Status: Pending Scan",
                                 bg=CARD, fg=GOLD, font=(FONT, 10, "bold"))
        self.cv_badge.pack(anchor="w", pady=4)

        btn_row = tk.Frame(cv_frame, bg=CARD)
        btn_row.pack(fill="x", pady=8)
        tk.Button(btn_row, text="🔬 Run CV Freshness Scan", bg=BLUE, fg=TEXT,
                  font=(FONT, 10, "bold"), bd=0, padx=12, pady=6, cursor="hand2",
                  command=self._run_cv_scan).pack(side="left")

        # Bottom Publish Button
        pub_frame = tk.Frame(parent, bg=CARD)
        pub_frame.pack(fill="x", padx=12, pady=10)
        tk.Button(pub_frame, text="🚀 Publish Surplus to Marketplace", bg=ACCENT, fg=TEXT,
                  font=(FONT, 11, "bold"), bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._publish_surplus).pack(anchor="w")

    def _on_price_type_change(self):
        if self.price_type.get() == "discounted":
            self.row_disc.pack(fill="x", pady=4)
        else:
            self.row_disc.pack_forget()

    def _run_cv_scan(self):
        """Simulates Computer Vision quality inspection of food tray."""
        item = self.item_name.get().strip() or "Food"
        # Simulate neural net detection score
        freshness_pct = random.randint(91, 99)
        self._cv_scan_done = True
        self._cv_score = 5 if freshness_pct >= 90 else 4

        self.cv_preview.config(bg="#0f2b1d")
        self.cv_status_lbl.config(
            bg="#0f2b1d", fg="#86efac",
            text=f"✔ CV Analysis Complete: '{item}'\n"
                 f"• Texture Consistency: High  • Color Spectrum: Natural\n"
                 f"• Freshness Index: {freshness_pct}% (Certified Safe for Distribution)"
        )
        self.cv_badge.config(text="✔ Quality Status: Certified Fresh & Safe", fg=HIGHLIGHT)
        messagebox.showinfo("CV Inspection Passed",
                            f"Food safety inspection passed!\nFreshness score: {freshness_pct}%\nSafe to distribute.")

    def _publish_surplus(self):
        if not self._cv_scan_done:
            ans = messagebox.askyesno("CV Quality Alert",
                                      "You haven't run the CV quality scan yet.\n"
                                      "Would you like to run automated inspection and proceed?")
            if ans:
                self._run_cv_scan()
            else:
                return

        item = self.item_name.get().strip()
        if not item:
            messagebox.showerror("Error", "Please enter food item name.")
            return

        try:
            qty = float(self.qty_var.get().strip())
            hours = float(self.exp_hours.get().strip())
            disc_p = float(self.disc_rate.get().strip()) if self.price_type.get() == "discounted" else 0.0
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for quantity/hours/price.")
            return

        expiry = datetime.now() + timedelta(hours=hours)

        # Coordinate jitter for demonstration
        lat = 12.9716 + random.uniform(-0.02, 0.02)
        lon = 77.5946 + random.uniform(-0.02, 0.02)

        lid = db.add_surplus_listing(
            seller_id=self.user["id"],
            item_name=item,
            category=self.cat_var.get(),
            total_quantity=qty,
            available_qty=qty,
            unit=self.unit_var.get(),
            expiry_datetime=expiry,
            price_type=self.price_type.get(),
            original_price=disc_p * 1.5,
            discounted_price=disc_p,
            location_address=self.loc_var.get().strip(),
            latitude=lat,
            longitude=lon,
            quality_status="verified_fresh",
            quality_score=self._cv_score
        )

        messagebox.showinfo("Published Successfully",
                            f"Surplus listing #{lid} published!\nAvailable to NGOs and local buyers.")
        self._cv_scan_done = False
        self.cv_status_lbl.config(bg="#0d1b2a", fg=MUTED,
                                  text="📷 No image scanned yet.\nClick 'Run CV Inspection' below.")
        self.cv_badge.config(text="⏳ Quality Status: Pending Scan", fg=GOLD)

    # ── TAB 2: Active Listings & Orders ──────────────────────────
    def _tab_listings_orders(self, parent):
        tk.Label(parent, text="Your Surplus Listings & Order Dispatches",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

        # Top section: My active listings
        tk.Label(parent, text="Active Surplus Stock:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(6, 2))
        self.listings_tree = make_tree(parent,
                                       columns=("ID", "Item", "Category", "Available", "Unit", "Price Type", "Rate", "Expires At", "Status"),
                                       col_widths=[50, 160, 100, 80, 60, 90, 80, 130, 90], height=5)

        # Bottom section: Incoming orders
        tk.Label(parent, text="Incoming NGO Bulk Reservations & Buyer Orders:",
                 bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.orders_tree = make_tree(parent,
                                     columns=("Order ID", "Item", "Buyer Name", "Role", "Qty Ordered", "Token", "Slot", "Status"),
                                     col_widths=[70, 150, 130, 80, 90, 90, 130, 90], height=6)

        # Action bar to verify pickup
        action_bar = tk.Frame(parent, bg=CARD)
        action_bar.pack(fill="x", padx=12, pady=8)

        lbl(action_bar, "Enter Pickup Token to Hand Over Food:").pack(side="left")
        self.verify_token_var = tk.StringVar()
        ent(action_bar, self.verify_token_var, 12).pack(side="left", padx=8)

        tk.Button(action_bar, text="✔ Verify & Mark Picked Up", bg=ACCENT, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=12, pady=5, cursor="hand2",
                  command=self._verify_pickup).pack(side="left", padx=4)

        tk.Button(action_bar, text="🔄 Refresh Tables", bg=SIDEBAR, fg=HIGHLIGHT,
                  font=(FONT, 9), bd=0, padx=10, pady=5, cursor="hand2",
                  command=self._load_listings_orders).pack(side="right")

        self._load_listings_orders()

    def _load_listings_orders(self):
        # Refresh listings
        self.listings_tree.delete(*self.listings_tree.get_children())
        rows = db.get_kitchen_listings(self.user["id"])
        for r in rows:
            rate_str = "Free" if r["price_type"] == 'free' else f"₹{r['discounted_price']}"
            exp_str = str(r["expiry_datetime"])[:16]
            self.listings_tree.insert("", "end", values=(
                r["id"], r["item_name"], r["category"],
                f"{float(r['available_qty']):.1f}", r["unit"],
                r["price_type"].capitalize(), rate_str, exp_str, r["status"]
            ))

        # Refresh orders
        self.orders_tree.delete(*self.orders_tree.get_children())
        orders = db.get_orders_for_seller(self.user["id"])
        for o in orders:
            slot_str = str(o["pickup_slot"])[:16]
            self.orders_tree.insert("", "end", iid=str(o["id"]), values=(
                o["id"], o["item_name"], o["buyer_name"], o["buyer_role"].upper(),
                f"{float(o['quantity_ordered']):.1f} {o['unit']}",
                o["pickup_token"], slot_str, o["status"].upper()
            ))

    def _verify_pickup(self):
        sel = self.orders_tree.selection()
        token = self.verify_token_var.get().strip()

        if not sel and not token:
            messagebox.showinfo("Select", "Select an order from the table or type the pickup token.")
            return

        order_id = int(sel[0]) if sel else None
        try:
            db.complete_pickup_order(order_id, pickup_token=token if token else None)
            messagebox.showinfo("Handover Confirmed",
                                "Pickup token verified! Order marked as completed.\nEco-Points credited.")
            self.verify_token_var.set("")
            self._load_listings_orders()
            self._refresh_points_banner()
        except Exception as e:
            messagebox.showerror("Verification Failed", str(e))

    # ── TAB 3: Circular Waste Diversion (Biogas / Farms) ─────────
    def _tab_circular_diversion(self, parent):
        tk.Label(parent, text="Circular Economy Waste Diversion Engine",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(parent,
                 text="Unsold edible batches or non-edible organic scraps should never end up in landfills.\n"
                      "Redirect cooked leftovers to Biogas Plants (for bio-methane & energy points) or vegetable peels to Organic Farms (for compost).",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 8))

        form = tk.LabelFrame(parent, text=" Dispatch Organic Waste ", bg=CARD, fg=HIGHLIGHT,
                             font=(FONT, 10, "bold"), padx=12, pady=10)
        form.pack(fill="x", padx=12, pady=6)

        row1 = tk.Frame(form, bg=CARD)
        row1.pack(fill="x", pady=4)
        lbl(row1, "Destination Channel:", width=18, anchor="w").pack(side="left")
        self.dest_var = tk.StringVar(value="biogas_plant")
        tk.Radiobutton(row1, text="⚡ GreenPower Biogas Plant (Cooked Leftovers)",
                       variable=self.dest_var, value="biogas_plant",
                       bg=CARD, fg=HIGHLIGHT, selectcolor=SIDEBAR,
                       command=self._update_diversion_calc).pack(side="left", padx=(0, 14))
        tk.Radiobutton(row1, text="🌱 AgroGreen Farm (Vegetable Scraps / Cattle Feed)",
                       variable=self.dest_var, value="organic_farm",
                       bg=CARD, fg=TEXT, selectcolor=SIDEBAR,
                       command=self._update_diversion_calc).pack(side="left")

        row2 = tk.Frame(form, bg=CARD)
        row2.pack(fill="x", pady=4)
        lbl(row2, "Waste Description:", width=18, anchor="w").pack(side="left")
        self.waste_type_var = tk.StringVar(value="unsold_cooked_food")
        self.waste_cb = ttk.Combobox(row2, textvariable=self.waste_type_var,
                                     values=["unsold_cooked_food", "spoiled_edible", "vegetable_scraps", "fpu_organic_sludge"],
                                     state="readonly", width=22)
        self.waste_cb.pack(side="left", padx=(0, 16))

        lbl(row2, "Quantity (kg):").pack(side="left")
        self.div_qty = tk.StringVar(value="25.0")
        self.div_qty.trace_add("write", lambda *args: self._update_diversion_calc())
        ent(row2, self.div_qty, 10).pack(side="left", padx=6)

        # Real-time conversion preview
        self.div_preview_lbl = tk.Label(form, text="Calculated Value: 4.25 m³ Biogas | +125 Energy Points",
                                        bg=SIDEBAR, fg=GOLD, font=(FONT, 10, "bold"), padx=10, pady=6)
        self.div_preview_lbl.pack(anchor="w", pady=8)

        tk.Button(form, text="♻️ Confirm Waste Dispatch & Claim Credits", bg=ACCENT, fg=TEXT,
                  font=(FONT, 10, "bold"), bd=0, padx=16, pady=6, cursor="hand2",
                  command=self._dispatch_waste).pack(anchor="w")

        # Table of past diversions
        tk.Label(parent, text="Recent Circular Waste Diversion Logs:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(12, 2))
        self.div_tree = make_tree(parent,
                                  columns=("ID", "Destination", "Partner Name", "Waste Type", "Quantity (kg)", "Credits/Points", "Date", "Status"),
                                  col_widths=[50, 120, 160, 150, 100, 110, 100, 90], height=6)
        self._load_diversions()

    def _update_diversion_calc(self):
        try:
            qty = float(self.div_qty.get().strip() or "0")
        except ValueError:
            qty = 0.0

        if self.dest_var.get() == "biogas_plant":
            m3 = round(qty * 0.17, 2)
            pts = int(qty * 5)
            self.div_preview_lbl.config(text=f"Calculated Yield: ≈ {m3} m³ Bio-Methane Energy | +{pts} Energy Points awarded")
        else:
            credit = round(qty * 4.0, 2)
            pts = int(qty * 3)
            self.div_preview_lbl.config(text=f"Calculated Yield: ≈ ₹{credit} Compost Value | +{pts} Soil Points awarded")

    def _dispatch_waste(self):
        try:
            qty = float(self.div_qty.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter valid quantity in kg.")
            return

        dest = self.dest_var.get()
        partner = "GreenPower Biogas Unit #4" if dest == "biogas_plant" else "AgroGreen Organic Valley Farm"
        pts = int(qty * 5) if dest == "biogas_plant" else int(qty * 3)
        credit = 0.0 if dest == "biogas_plant" else round(qty * 4.0, 2)

        did = db.record_circular_diversion(
            kitchen_id=self.user["id"],
            waste_type=self.waste_type_var.get(),
            destination_type=dest,
            partner_name=partner,
            quantity_kg=qty,
            energy_points=pts,
            financial_credit=credit
        )
        messagebox.showinfo("Waste Diverted",
                            f"Waste dispatch #{did} scheduled successfully!\n"
                            f"Earned {pts} points for zero-landfill diversion.")
        self._load_diversions()
        self._refresh_points_banner()

    def _load_diversions(self):
        self.div_tree.delete(*self.div_tree.get_children())
        rows = db.get_circular_diversions(self.user["id"])
        for r in rows:
            dest_name = "Biogas Plant" if r["destination_type"] == "biogas_plant" else "Organic Farm"
            credit_txt = f"{r['energy_points']} pts" if r["destination_type"] == "biogas_plant" else f"₹{r['financial_credit']}"
            self.div_tree.insert("", "end", values=(
                r["id"], dest_name, r["partner_name"], r["waste_type"],
                f"{float(r['quantity_kg']):.1f} kg", credit_txt,
                str(r["diversion_date"]), r["status"].upper()
            ))

    # ── TAB 4: Rewards & Impact Ledger ───────────────────────────
    def _tab_rewards_ledger(self, parent):
        tk.Label(parent, text="Eco-Rewards & Sustainability Impact Ledger",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        # KPI Summary Cards
        kpi_frame = tk.Frame(parent, bg=CARD)
        kpi_frame.pack(fill="x", padx=12, pady=6)

        metrics = db.get_sustainability_metrics(self.user["id"])
        total_pts = db.get_user_points(self.user["id"])

        cards = [
            ("🌟 Eco-Points", f"{total_pts} pts", "#f59e0b"),
            ("🍲 Food Redistributed", f"{metrics['total_food_redistributed_kg']:.1f} kg", "#10b981"),
            ("🍃 CO2e Avoided", f"{metrics['co2_avoided_kg']} kg", "#3b82f6"),
            ("⚡ Biogas Produced", f"{metrics['biogas_m3_generated']} m³", "#ec4899"),
        ]
        for title, val, color in cards:
            card = tk.Frame(kpi_frame, bg=SIDEBAR, padx=16, pady=12, relief="solid", bd=1)
            card.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(card, text=title, bg=SIDEBAR, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
            tk.Label(card, text=val, bg=SIDEBAR, fg=color, font=(FONT, 15, "bold")).pack(anchor="w", pady=(4, 0))

        # Points History Table
        tk.Label(parent, text="Reward Points Audit Trail:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(14, 2))
        self.rewards_tree = make_tree(parent,
                                      columns=("ID", "Points", "Activity Reason", "Balance After", "Recorded At"),
                                      col_widths=[60, 90, 220, 110, 150], height=8)
        self._load_rewards()

    def _load_rewards(self):
        self.rewards_tree.delete(*self.rewards_tree.get_children())
        rows = db.get_points_history(self.user["id"])
        for r in rows:
            pts_sign = f"+{r['points']}" if r["points"] > 0 else str(r["points"])
            self.rewards_tree.insert("", "end", values=(
                r["id"], pts_sign, r["reason"].replace("_", " ").title(),
                r["balance_after"], str(r["created_at"])[:16]
            ))

    # ── TAB 5: User Manual ───────────────────────────────────────
    def _tab_manual(self, parent):
        tk.Label(parent, text="Kitchen & FPU Operational Guidelines",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        content = db.get_manual("kitchen_fpu")

        txt = tk.Text(parent, bg=SIDEBAR, fg=TEXT, font=(FONT, 10), wrap="word",
                      padx=14, pady=12, relief="solid", bd=1)
        txt.pack(fill="both", expand=True, padx=12, pady=8)
        txt.insert("1.0", content)
        txt.config(state="disabled")
