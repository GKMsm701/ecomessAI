"""
staff_dash.py - EcoMess Staff Dashboard
Tabs: Menu | Salary | Poll Data | Food Prepared | Inventory | Food Waste | Feedback | Manual
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import date, timedelta

import database as db

CARD      = "#1f3040"
SIDEBAR   = "#0d1b2a"
ACCENT    = "#2d6a4f"
ACCENT2   = "#40916c"
HIGHLIGHT = "#74c69d"
TEXT      = "#edf2f4"
MUTED     = "#94a3b8"
RED       = "#e63946"
GOLD      = "#f4d03f"
FONT      = "Segoe UI"

DAYS   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MEALS  = ["Breakfast","Lunch","Snacks","Dinner"]
MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

MEAL_COLORS = {
    "Breakfast": "#f59e0b",
    "Lunch":     "#3b82f6",
    "Snacks":    "#10b981",
    "Dinner":    "#8b5cf6",
}


def get_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())


def make_tree(parent, columns, col_widths=None, height=10):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="both", expand=True, padx=8, pady=8)
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                         selectmode="browse", height=height)
    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths else 120
        tree.heading(col, text=col)
        tree.column(col, width=w, minwidth=50, anchor="center")
    sb_y = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    sb_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side="right",  fill="y")
    sb_x.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    return tree


# ──────────────────────────────────────────────────────────────
#  Canvas bar chart helper (used in poll data and similar)
# ──────────────────────────────────────────────────────────────
def draw_poll_chart(parent, poll_date, label_text):
    """Draw a meal-wise grouped bar chart on a Canvas for the given date."""
    outer = tk.LabelFrame(parent, text=f"  {label_text}  ",
                          bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold"))
    outer.pack(fill="x", padx=8, pady=6)

    summary = db.get_meal_poll_summary(poll_date)
    totals  = db.get_meal_poll_totals(poll_date)

    if not any(summary.values()):
        tk.Label(outer, text="No votes recorded for this date.",
                 bg=CARD, fg=MUTED, font=(FONT, 10)).pack(pady=14)
        return

    # Compact bar chart per meal
    for meal in MEALS:
        count    = summary.get(meal, 0)
        color    = MEAL_COLORS[meal]
        meal_row = tk.Frame(outer, bg=CARD)
        meal_row.pack(fill="x", padx=12, pady=3)

        tk.Label(meal_row, text=f"{meal}:", bg=CARD, fg=TEXT,
                 font=(FONT, 9, "bold"), width=12, anchor="w").pack(side="left")
        bar_w = min(count * 6, 280)
        tk.Frame(meal_row, bg=color, width=bar_w, height=20).pack(side="left")
        tk.Label(meal_row, text=f"  {count} students", bg=CARD, fg=MUTED,
                 font=(FONT, 9)).pack(side="left")

    # Top dishes per meal
    if totals:
        tk.Label(outer, text="Top dish votes:", bg=CARD, fg=MUTED,
                 font=(FONT, 8, "italic")).pack(anchor="w", padx=12, pady=(6, 0))
        by_meal = {}
        for row in totals:
            by_meal.setdefault(row["meal"], []).append(row)

        for meal in MEALS:
            if meal not in by_meal:
                continue
            top = by_meal[meal][0]
            tk.Label(outer,
                     text=f"   {meal}: {top['dish']} ({top['votes']} votes)",
                     bg=CARD, fg=TEXT, font=(FONT, 9)).pack(anchor="w", padx=20)


# ──────────────────────────────────────────────────────────────
#  Staff Dashboard
# ──────────────────────────────────────────────────────────────
class StaffDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app  = app
        self.user = app.current_user
        self.inst_type = (self.user.get('institution_type') or 'general').lower()
        self.category  = db.get_kitchen_category(self.inst_type)
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT2, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        cat_name = "🏫 Institution Staff" if self.category == 'institutional' else "🍳 Private Kitchen Staff"
        inst_label = self.inst_type.replace('_', ' ').title()
        tk.Label(header,
                 text=f"{cat_name} ({inst_label}) — {self.user.get('full_name') or self.user['username']}",
                 bg=ACCENT2, fg=TEXT, font=(FONT, 13, "bold")).pack(side="left", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tabs_base = [
            ("Menu",          self._tab_menu),
            ("Salary",        self._tab_salary),
        ]
        tabs_end = [
            ("Food Prepared", self._tab_food_prepared),
            ("Inventory",     self._tab_inventory),
            ("Food Waste",    self._tab_foodwaste),
            ("Feedback",      self._tab_feedback),
            ("User Manual",   self._tab_manual),
        ]

        if self.category == 'private_kitchen':
            tabs_mid = [("Orders Queue", self._tab_customer_orders_queue)]
        else:
            tabs_mid = [("Poll Data", self._tab_polldata)]

        tabs = tabs_base + tabs_mid + tabs_end
        for label, builder in tabs:
            frame = tk.Frame(notebook, bg=CARD)
            notebook.add(frame, text=f"  {label}  ")
            builder(frame)

    # ── Menu ───────────────────────────────────────────────────
    def _tab_menu(self, parent):
        self.menu_day_idx = 0
        week_start = get_week_start()
        self.menu_data = db.get_menu_for_week(week_start)

        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(ctrl, text="Weekly Menu", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(side="left")
        tk.Label(ctrl, text=f"(Week of {week_start})", bg=CARD, fg=MUTED,
                 font=(FONT, 9)).pack(side="left", padx=8)

        nav = tk.Frame(parent, bg=CARD)
        nav.pack(fill="x", padx=12, pady=4)
        tk.Button(nav, text="< Prev", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._menu_nav(-1)).pack(side="left")
        self.day_label = tk.Label(nav, text="", bg=CARD, fg=TEXT,
                                   font=(FONT, 11, "bold"), width=14)
        self.day_label.pack(side="left", padx=20)
        tk.Button(nav, text="Next >", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._menu_nav(1)).pack(side="left")

        self.menu_card = tk.Frame(parent, bg=SIDEBAR)
        self.menu_card.pack(fill="both", expand=True, padx=20, pady=10)
        self._render_menu_day()

    def _menu_nav(self, delta):
        self.menu_day_idx = (self.menu_day_idx + delta) % 7
        self._render_menu_day()

    def _render_menu_day(self):
        for w in self.menu_card.winfo_children():
            w.destroy()
        day = DAYS[self.menu_day_idx]
        self.day_label.config(text=day)
        day_items = [r for r in self.menu_data if r["day_of_week"] == day]
        if not day_items:
            tk.Label(self.menu_card, text="No menu set for this day",
                     bg=SIDEBAR, fg=MUTED, font=(FONT, 11)).pack(pady=30)
            return
        for meal in MEALS:
            entries = [r for r in day_items if r["meal_type"] == meal]
            line = tk.Frame(self.menu_card, bg=CARD)
            line.pack(fill="x", padx=16, pady=6)
            tk.Label(line, text=meal, bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold"),
                     width=10, anchor="w").pack(side="left", padx=8)
            tk.Label(line, text=entries[0]["items"] if entries else "-",
                     bg=CARD, fg=TEXT, font=(FONT, 10), anchor="w").pack(side="left", padx=8)

    # ── Salary ─────────────────────────────────────────────────
    def _tab_salary(self, parent):
        tk.Label(parent, text="Salary Details", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tree = make_tree(parent,
                         columns=("Month","Year","Amount (Rs)","Status","Paid Date"),
                         col_widths=[120, 80, 120, 100, 130])
        records = db.get_salary(user_id=self.user["id"])
        for row in records:
            tree.insert("", "end", values=(
                MONTHS[row["month"] - 1], row["year"],
                f"Rs {row['amount']:.2f}", row["status"].capitalize(),
                str(row["paid_date"]) if row["paid_date"] else "-",
            ))
        if not records:
            tree.insert("", "end", values=("No salary records", "", "", "", ""))

    # ── Poll Data (today + tomorrow graphs) ────────────────────
    def _tab_polldata(self, parent):
        self._pd_parent = parent
        self._render_polldata()

    def _render_polldata(self):
        parent = self._pd_parent
        for w in parent.winfo_children():
            w.destroy()

        today    = date.today()
        tomorrow = today + timedelta(days=1)

        tk.Label(parent, text="Student Poll Data — Meal-wise Headcounts",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(parent,
                 text="Today's data: students polled yesterday for today's meals.  |  "
                      "Tomorrow's data: students currently placing their votes.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 8))

        # Canvas scroll container
        wrapper = tk.Frame(parent, bg=CARD)
        wrapper.pack(fill="both", expand=True, padx=8, pady=4)
        canvas    = tk.Canvas(wrapper, bg=CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        inner = tk.Frame(canvas, bg=CARD)
        wid   = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(wid, width=e.width))

        draw_poll_chart(inner, today,
                        f"Today's Poll — {today.strftime('%A, %d %b %Y')} (votes submitted yesterday)")
        draw_poll_chart(inner, tomorrow,
                        f"Tomorrow's Live Poll — {tomorrow.strftime('%A, %d %b %Y')} (actively polling)")

        tk.Button(parent, text="🔄 Refresh", bg=ACCENT, fg=TEXT, bd=0, padx=12, pady=5,
                  cursor="hand2", command=self._render_polldata).pack(anchor="w", padx=12, pady=6)

    # ── Food Prepared ──────────────────────────────────────────
    def _tab_food_prepared(self, parent):
        tk.Label(parent, text="Record Food Prepared Today",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        form = tk.LabelFrame(parent, text=" New Entry ", bg=CARD, fg=HIGHLIGHT,
                              font=(FONT, 9, "bold"))
        form.pack(fill="x", padx=12, pady=6)

        def lbl(p, t): return tk.Label(p, text=t, bg=CARD, fg=MUTED, font=(FONT, 9))
        def ent(p, v, w=16):
            return tk.Entry(p, textvariable=v, bg=SIDEBAR, fg=TEXT, font=(FONT, 10),
                            relief="solid", bd=1, width=w, insertbackground=TEXT)

        row1 = tk.Frame(form, bg=CARD); row1.pack(fill="x", padx=8, pady=4)
        lbl(row1, "Date (YYYY-MM-DD):").pack(side="left")
        self.fp_date = tk.StringVar(value=str(date.today()))
        ent(row1, self.fp_date, 14).pack(side="left", padx=(4, 18))

        lbl(row1, "Meal:").pack(side="left")
        self.fp_meal = tk.StringVar(value="Lunch")
        ttk.Combobox(row1, textvariable=self.fp_meal, values=MEALS,
                     state="readonly", width=10).pack(side="left", padx=(4, 18))

        lbl(row1, "Item Name:").pack(side="left")
        self.fp_item = tk.StringVar()
        ent(row1, self.fp_item, 20).pack(side="left", padx=(4, 0))

        row2 = tk.Frame(form, bg=CARD); row2.pack(fill="x", padx=8, pady=4)
        lbl(row2, "Quantity Made:").pack(side="left")
        self.fp_qty = tk.StringVar()
        ent(row2, self.fp_qty, 8).pack(side="left", padx=(4, 18))

        lbl(row2, "Unit:").pack(side="left")
        self.fp_unit = tk.StringVar(value="kg")
        ttk.Combobox(row2, textvariable=self.fp_unit,
                     values=["kg", "L", "pcs", "g", "ml", "dozen"],
                     state="readonly", width=8).pack(side="left", padx=(4, 18))

        lbl(row2, "Servings (portions):").pack(side="left")
        self.fp_servings = tk.StringVar(value="0")
        ent(row2, self.fp_servings, 6).pack(side="left", padx=(4, 0))

        tk.Button(parent, text="Submit Food Prepared Entry", bg=ACCENT, fg=TEXT,
                  bd=0, padx=14, pady=7, cursor="hand2",
                  command=self._submit_food_prepared).pack(anchor="w", padx=12, pady=6)

        tk.Label(parent, text="Recent Entries (by this staff):", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        self.fp_tree = make_tree(parent,
                                  columns=("Date","Meal","Item","Qty Made","Unit","Servings"),
                                  col_widths=[110, 100, 160, 90, 70, 90], height=8)
        self._load_fp_tree()

    def _load_fp_tree(self):
        self.fp_tree.delete(*self.fp_tree.get_children())
        records = db.get_food_prepared_staff(self.user["id"])
        for row in records:
            self.fp_tree.insert("", "end", values=(
                str(row["prep_date"]), row["meal_type"], row["item_name"],
                row["quantity_made"], row["unit"] or "-", row["servings"],
            ))
        if not records:
            self.fp_tree.insert("", "end", values=("-", "No entries yet", "", "", "", ""))

    def _submit_food_prepared(self):
        try:
            prep_date = self.fp_date.get().strip()
            meal_type = self.fp_meal.get()
            item_name = self.fp_item.get().strip()
            qty       = float(self.fp_qty.get().strip())
            unit      = self.fp_unit.get()
            servings  = int(self.fp_servings.get().strip())
            if not item_name:
                raise ValueError("Item name is required.")
        except ValueError as err:
            messagebox.showerror("Input Error", str(err))
            return
        db.add_food_prepared(self.user["id"], prep_date, meal_type, item_name, qty, unit, servings)
        messagebox.showinfo("Recorded", "Food prepared entry saved successfully.")
        self.fp_item.set("")
        self.fp_qty.set("")
        self.fp_servings.set("0")
        self._load_fp_tree()

    # ── Inventory (view + use/deduct) ──────────────────────────
    def _tab_inventory(self, parent):
        tk.Label(parent, text="Inventory", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        # Read-only view
        self.inv_tree = make_tree(parent,
                                   columns=("ID","Item","Quantity","Unit","Last Updated"),
                                   col_widths=[60, 180, 100, 80, 160], height=8)
        self._load_inv_tree()
        tk.Button(parent, text="🔄 Refresh Inventory", bg=ACCENT, fg=TEXT, bd=0,
                  padx=10, pady=4, cursor="hand2",
                  command=self._load_inv_tree).pack(anchor="w", padx=12, pady=(0, 6))

        # Usage / Deduction form
        use_frame = tk.LabelFrame(parent, text=" Record Daily Usage (deducts from inventory) ",
                                   bg=CARD, fg=RED, font=(FONT, 9, "bold"))
        use_frame.pack(fill="x", padx=12, pady=6)

        def lbl(p, t): return tk.Label(p, text=t, bg=CARD, fg=MUTED, font=(FONT, 9))
        def ent(p, v, w=16):
            return tk.Entry(p, textvariable=v, bg=SIDEBAR, fg=TEXT, font=(FONT, 10),
                            relief="solid", bd=1, width=w, insertbackground=TEXT)

        row1 = tk.Frame(use_frame, bg=CARD); row1.pack(fill="x", padx=8, pady=4)
        lbl(row1, "Select Item:").pack(side="left")
        self.use_item_var = tk.StringVar()
        self.use_item_cb  = ttk.Combobox(row1, textvariable=self.use_item_var,
                                          state="readonly", width=22)
        self.use_item_cb.pack(side="left", padx=(4, 18))
        self._reload_inv_dropdown()

        lbl(row1, "Quantity Used:").pack(side="left")
        self.use_qty  = tk.StringVar()
        ent(row1, self.use_qty, 8).pack(side="left", padx=(4, 18))

        lbl(row1, "Date:").pack(side="left")
        self.use_date = tk.StringVar(value=str(date.today()))
        ent(row1, self.use_date, 12).pack(side="left", padx=(4, 0))

        row2 = tk.Frame(use_frame, bg=CARD); row2.pack(fill="x", padx=8, pady=4)
        lbl(row2, "Note (optional):").pack(side="left")
        self.use_note = tk.StringVar()
        ent(row2, self.use_note, 40).pack(side="left", padx=(4, 0))

        tk.Button(parent, text="Submit Usage (Deduct from Inventory)", bg=RED, fg=TEXT,
                  bd=0, padx=14, pady=7, cursor="hand2",
                  command=self._submit_usage).pack(anchor="w", padx=12, pady=6)

        tk.Label(parent, text="Recent Usage Log (your entries):", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(6, 2))
        self.usage_tree = make_tree(parent,
                                     columns=("Date","Item","Qty Used","Unit","Note"),
                                     col_widths=[110, 160, 90, 70, 220], height=5)
        self._load_usage_tree()

    def _load_inv_tree(self):
        self.inv_tree.delete(*self.inv_tree.get_children())
        items = db.get_inventory()
        for item in items:
            self.inv_tree.insert("", "end", iid=str(item["id"]),
                                 values=(item["id"], item["item_name"],
                                         item["quantity"], item["unit"] or "-",
                                         str(item["updated_at"])[:16]))
        if not items:
            self.inv_tree.insert("", "end", values=("-", "No inventory records", "", "", ""))
        self._reload_inv_dropdown()

    def _reload_inv_dropdown(self):
        items = db.get_inventory()
        self._inv_map = {f"{i['item_name']} ({i['id']})": i["id"] for i in items}
        if hasattr(self, "use_item_cb"):
            self.use_item_cb["values"] = list(self._inv_map.keys())

    def _submit_usage(self):
        try:
            item_label = self.use_item_var.get()
            if not item_label:
                raise ValueError("Please select an inventory item.")
            item_id  = self._inv_map[item_label]
            used_qty = float(self.use_qty.get().strip())
            if used_qty <= 0:
                raise ValueError("Quantity must be greater than 0.")
            usage_date = self.use_date.get().strip()
            note       = self.use_note.get().strip()
        except (ValueError, KeyError) as err:
            messagebox.showerror("Input Error", str(err))
            return
        try:
            db.use_inventory_item(self.user["id"], item_id, used_qty, usage_date, note)
            messagebox.showinfo("Recorded",
                f"Usage recorded. {used_qty} units deducted from inventory.")
            self.use_qty.set("")
            self.use_note.set("")
            self._load_inv_tree()
            self._load_usage_tree()
        except ValueError as err:
            messagebox.showerror("Error", str(err))

    def _load_usage_tree(self):
        today   = date.today()
        from_d  = today - timedelta(days=30)
        self.usage_tree.delete(*self.usage_tree.get_children())
        records = db.get_inventory_usage(from_date=from_d, to_date=today)
        # Filter to this staff only
        records = [r for r in records if r.get("staff_id") == self.user["id"]
                   or r.get("staff_name") == (self.user.get("full_name") or self.user["username"])]
        for row in records:
            self.usage_tree.insert("", "end", values=(
                str(row["usage_date"]), row["item_name"],
                row["used_qty"], row["unit"] or "-", row["note"] or "",
            ))
        if not records:
            self.usage_tree.insert("", "end", values=("-", "No usage records", "", "", ""))

    # ── Food Waste ─────────────────────────────────────────────
    def _tab_foodwaste(self, parent):
        tk.Label(parent, text="Record Food Waste", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=16, pady=8)

        def lbl(text):
            return tk.Label(form, text=text, bg=CARD, fg=MUTED, font=(FONT, 9))
        def entry(var, width=20):
            return tk.Entry(form, textvariable=var, bg=SIDEBAR, fg=TEXT, font=(FONT, 10),
                            relief="solid", bd=1, width=width, insertbackground=TEXT)

        row1 = tk.Frame(form, bg=CARD); row1.pack(fill="x", pady=4)
        lbl("Date (YYYY-MM-DD)").pack(side="left", padx=(0, 8))
        self.fw_date = tk.StringVar(value=str(date.today()))
        entry(self.fw_date, 14).pack(side="left", padx=(0, 24))
        lbl("Item Name").pack(side="left", padx=(0, 8))
        self.fw_item = tk.StringVar()
        entry(self.fw_item, 22).pack(side="left", padx=(0, 24))

        row2 = tk.Frame(form, bg=CARD); row2.pack(fill="x", pady=4)
        lbl("Quantity").pack(side="left", padx=(0, 8))
        self.fw_qty  = tk.StringVar()
        entry(self.fw_qty, 10).pack(side="left", padx=(0, 24))
        lbl("Unit (kg/L/pcs)").pack(side="left", padx=(0, 8))
        self.fw_unit = tk.StringVar(value="kg")
        ttk.Combobox(form, textvariable=self.fw_unit,
                     values=["kg", "L", "pcs", "g", "ml"],
                     width=8, state="readonly").pack(side="left")

        tk.Button(parent, text="Submit Waste Entry", bg=RED, fg=TEXT,
                  bd=0, padx=14, pady=7, cursor="hand2",
                  command=self._submit_waste).pack(anchor="w", padx=16, pady=6)

        tk.Label(parent, text="Recent Food Waste Entries:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.waste_tree = make_tree(parent,
                                     columns=("Date","Item","Quantity","Unit"),
                                     col_widths=[120, 180, 100, 80])
        self._load_waste_tree()

    def _load_waste_tree(self):
        self.waste_tree.delete(*self.waste_tree.get_children())
        records = db.get_food_waste(staff_id=self.user["id"])
        for row in records:
            self.waste_tree.insert("", "end", values=(
                str(row["waste_date"]), row["item_name"],
                row["quantity"], row["unit"] or "-",
            ))
        if not records:
            self.waste_tree.insert("", "end", values=("No records", "", "", ""))

    def _submit_waste(self):
        try:
            waste_date = self.fw_date.get().strip()
            item_name  = self.fw_item.get().strip()
            quantity   = float(self.fw_qty.get().strip())
            unit       = self.fw_unit.get().strip()
            if not item_name:
                raise ValueError("Item name is required.")
        except ValueError as err:
            messagebox.showerror("Input Error", str(err))
            return
        db.add_food_waste(self.user["id"], waste_date, item_name, quantity, unit)
        messagebox.showinfo("Recorded", "Food waste entry recorded successfully.")
        self.fw_item.set("")
        self.fw_qty.set("")
        self._load_waste_tree()

    # ── Feedback (view-only) ───────────────────────────────────
    def _tab_feedback(self, parent):
        tk.Label(parent, text="Student Feedback", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        # Summary
        avg  = db.get_avg_rating()
        dist = db.get_rating_distribution()
        total = sum(dist.values())

        summary = tk.Frame(parent, bg=SIDEBAR)
        summary.pack(fill="x", padx=12, pady=6)

        tk.Label(summary, text=f"⭐  Average Rating: {avg:.1f} / 5.0",
                 bg=SIDEBAR, fg=GOLD, font=(FONT, 14, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(summary, text=f"Total submissions: {total}",
                 bg=SIDEBAR, fg=MUTED, font=(FONT, 9)).pack(side="left", padx=8)

        # Distribution mini-bar
        dist_frame = tk.Frame(parent, bg=CARD)
        dist_frame.pack(fill="x", padx=12, pady=4)
        for star in range(5, 0, -1):
            cnt  = dist[star]
            row  = tk.Frame(dist_frame, bg=CARD)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{'★'*star}{'☆'*(5-star)}", bg=CARD, fg=GOLD,
                     font=(FONT, 9), width=12, anchor="w").pack(side="left")
            bar_w = int((cnt / max(total, 1)) * 200)
            tk.Frame(row, bg=ACCENT2, width=bar_w, height=14).pack(side="left")
            tk.Label(row, text=f"  {cnt}", bg=CARD, fg=MUTED,
                     font=(FONT, 9)).pack(side="left")

        # Full table
        tk.Label(parent, text="All Feedback Entries:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tree = make_tree(parent,
                         columns=("Date","Student","Rating","Comment"),
                         col_widths=[110, 160, 80, 360])
        for row in db.get_all_feedback():
            stars = "★" * row["rating"] + "☆" * (5 - row["rating"])
            tree.insert("", "end", values=(
                str(row["created_at"])[:10],
                row["full_name"] or row["username"],
                stars, (row["comment"] or "")[:100],
            ))

    # ── Manual ─────────────────────────────────────────────────
    def _tab_manual(self, parent):
        tk.Label(parent, text="User Manual", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        text = scrolledtext.ScrolledText(parent, bg=SIDEBAR, fg=TEXT, font=(FONT, 10),
                                         wrap="word", relief="flat", bd=0)
        text.pack(fill="both", expand=True, padx=12, pady=8)
        text.insert("1.0", db.get_manual("staff"))
        text.config(state="disabled")

    # ── Customer Orders Queue (Private Kitchen staff) ────────────
    def _tab_customer_orders_queue(self, parent):
        tk.Label(parent, text="📦 Customer Orders Queue",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(parent, text="Live orders from customers. Select an order and mark it as preparing or ready.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl_w = tk.Label(ctrl, text="Filter:", bg=CARD, fg=MUTED, font=(FONT, 9))
        lbl_w.pack(side="left")
        self.sq_filter = tk.StringVar(value="placed")
        ttk.Combobox(ctrl, textvariable=self.sq_filter,
                     values=["all", "placed", "preparing", "ready_for_pickup", "completed"],
                     state="readonly", width=16).pack(side="left", padx=6)
        tk.Button(ctrl, text="Refresh", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_sq).pack(side="left", padx=4)

        self.sq_tree = make_tree(parent,
            columns=("ID", "Token", "Customer", "Items", "Total (₹)", "Status", "Ordered At"),
            col_widths=[50, 80, 130, 220, 90, 130, 130], height=10)

        upd = tk.Frame(parent, bg=CARD)
        upd.pack(fill="x", padx=12, pady=6)
        tk.Label(upd, text="Update status:", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side="left")
        self.sq_new_status = tk.StringVar(value="preparing")
        ttk.Combobox(upd, textvariable=self.sq_new_status,
                     values=["preparing", "ready_for_pickup", "completed", "cancelled"],
                     state="readonly", width=16).pack(side="left", padx=6)
        tk.Button(upd, text="✔ Mark", bg=ACCENT2, fg=TEXT, bd=0, padx=12, pady=4,
                  cursor="hand2", command=self._mark_sq_status).pack(side="left", padx=4)

        self._load_sq()

    def _load_sq(self):
        self.sq_tree.delete(*self.sq_tree.get_children())
        sf = self.sq_filter.get()
        # Staff sees their admin's orders (same kitchen_user_id chain)
        # We use the staff user's id but try to get all for their kitchen context
        orders = db.get_customer_orders(
            kitchen_user_id=self.user["id"],
            status=None if sf == "all" else sf
        )
        if not orders:
            # Try without kitchen filter for staff who may have different admin
            orders = db.get_customer_orders(status=None if sf == "all" else sf, limit=100)
        for o in orders:
            try:
                import json
                items = json.loads(o["items_json"].replace("'", '"'))
                item_str = ", ".join(f"{it.get('name','?')}×{it.get('qty',1)}" for it in items)
            except Exception:
                item_str = str(o["items_json"])[:60]
            self.sq_tree.insert("", "end", iid=str(o["id"]), values=(
                o["id"], o["pickup_token"], o["customer_name"],
                item_str, f"₹{float(o['total_amount']):.2f}",
                o["order_status"].replace("_"," ").title(),
                str(o["ordered_at"])[:16]
            ))

    def _mark_sq_status(self):
        sel = self.sq_tree.selection()
        if not sel:
            from tkinter import messagebox
            messagebox.showwarning("Select", "Select an order first.")
            return
        oid = int(sel[0])
        ns  = self.sq_new_status.get()
        db.update_customer_order_status(oid, ns)
        from tkinter import messagebox
        messagebox.showinfo("Updated", f"Order #{oid} → {ns.replace('_',' ').title()}")
        self._load_sq()

