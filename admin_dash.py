"""
admin_dash.py - EcoMess Admin Dashboard
Tabs: Menu | Users | Salary | Inventory | Food Waste | Poll Data | Feedback
      | Demand Prediction | Food Prepared | Complaints | Notifications | Manual
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
BLUE      = "#3b82f6"
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


def make_tree(parent, columns, col_widths=None, height=12):
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


def lbl(parent, text, **kwargs):
    defaults = dict(bg=CARD, fg=MUTED, font=(FONT, 9))
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def ent(parent, var, width=20):
    return tk.Entry(parent, textvariable=var, bg=SIDEBAR, fg=TEXT,
                    insertbackground=TEXT, font=(FONT, 10),
                    relief="solid", bd=1, width=width)


def draw_poll_chart(parent, poll_date, label_text):
    """Draw meal-wise bar chart + dish breakdown for a given poll_date."""
    outer = tk.LabelFrame(parent, text=f"  {label_text}  ",
                          bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold"))
    outer.pack(fill="x", padx=8, pady=6)

    summary = db.get_meal_poll_summary(poll_date)
    totals  = db.get_meal_poll_totals(poll_date)

    if not any(summary.values()):
        tk.Label(outer, text="No votes recorded for this date.",
                 bg=CARD, fg=MUTED, font=(FONT, 10)).pack(pady=14)
        return

    for meal in MEALS:
        count    = summary.get(meal, 0)
        color    = MEAL_COLORS[meal]
        meal_row = tk.Frame(outer, bg=CARD)
        meal_row.pack(fill="x", padx=12, pady=3)
        tk.Label(meal_row, text=f"{meal}:", bg=CARD, fg=TEXT,
                 font=(FONT, 9, "bold"), width=12, anchor="w").pack(side="left")
        bar_w = min(count * 6, 300)
        tk.Frame(meal_row, bg=color, width=bar_w, height=20).pack(side="left")
        tk.Label(meal_row, text=f"  {count} students", bg=CARD, fg=MUTED,
                 font=(FONT, 9)).pack(side="left")

    if totals:
        tk.Label(outer, text="Dish breakdown:", bg=CARD, fg=MUTED,
                 font=(FONT, 8, "italic")).pack(anchor="w", padx=12, pady=(8, 0))
        by_meal = {}
        for row in totals:
            by_meal.setdefault(row["meal"], []).append(row)
        for meal in MEALS:
            if meal not in by_meal:
                continue
            for row in by_meal[meal][:3]:  # top 3 dishes
                tk.Label(outer,
                         text=f"   {meal}: {row['dish']} — {row['votes']} votes",
                         bg=CARD, fg=TEXT, font=(FONT, 9)).pack(anchor="w", padx=20)


# ──────────────────────────────────────────────────────────────
#  Admin Dashboard
# ──────────────────────────────────────────────────────────────
class AdminDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app  = app
        self.user = app.current_user
        self.inst_type = (self.user.get('institution_type') or 'general').lower()
        self.category  = db.get_kitchen_category(self.inst_type)  # 'institutional' or 'private_kitchen'
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        header = tk.Frame(self, bg="#1b4332", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        cat_label = "🏫 Institution Admin" if self.category == 'institutional' else "🍽️ Private Kitchen Admin"
        inst_label = self.inst_type.replace('_', ' ').title()
        tk.Label(header,
                 text=f"{cat_label} ({inst_label}) — {self.user.get('full_name') or self.user['username']}",
                 bg="#1b4332", fg=TEXT, font=(FONT, 12, "bold")).pack(side="left", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Core tabs present in both categories
        tabs_common_start = [
            ("Menu",               self._tab_menu),
            ("Users",              self._tab_users),
            ("Salary",             self._tab_salary),
        ]
        tabs_common_end = [
            ("Inventory",          self._tab_inventory),
            ("Food Waste",         self._tab_foodwaste),
            ("Feedback",           self._tab_feedback),
            ("Demand Prediction",  self._tab_demand),
            ("Food Prepared",      self._tab_food_prepared),
            ("Complaints",         self._tab_complaints),
            ("Notifications",      self._tab_notifications),
            ("Post Surplus",       self._tab_post_surplus),
            ("Monthly Report",     self._tab_monthly_report),
            ("User Manual",        self._tab_manual),
        ]

        if self.category == 'institutional':
            tabs_category = [
                ("Mess Bills",  self._tab_mess_bills),
                ("Poll Data",   self._tab_polldata),
            ]
        else:  # private_kitchen
            tabs_category = [
                ("Customer Orders",  self._tab_customer_orders),
                ("Order Summary",    self._tab_order_summary),
            ]

        tabs = tabs_common_start + tabs_category + tabs_common_end
        for label, builder in tabs:
            frame = tk.Frame(notebook, bg=CARD)
            notebook.add(frame, text=f"  {label}  ")
            builder(frame)


    # ── Menu ───────────────────────────────────────────────────
    def _tab_menu(self, parent):
        def get_week_start():
            today = date.today()
            return today - timedelta(days=today.weekday())

        self.menu_week_start = tk.StringVar(value=str(get_week_start()))
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(ctrl, text="Menu - Week starting:", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(side="left")
        ent(ctrl, self.menu_week_start, 14).pack(side="left", padx=8)
        tk.Button(ctrl, text="Load", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_menu_tree).pack(side="left", padx=4)

        self.menu_tree = make_tree(parent,
                                    columns=("ID","Day","Meal","Items"),
                                    col_widths=[50, 120, 100, 400], height=10)
        self._load_menu_tree()

        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=12, pady=6)
        lbl(form, "Day:").pack(side="left")
        self.menu_day = tk.StringVar(value="Monday")
        ttk.Combobox(form, textvariable=self.menu_day, values=DAYS,
                     state="readonly", width=12).pack(side="left", padx=(4, 12))
        lbl(form, "Meal:").pack(side="left")
        self.menu_meal = tk.StringVar(value="Lunch")
        ttk.Combobox(form, textvariable=self.menu_meal, values=MEALS,
                     state="readonly", width=10).pack(side="left", padx=(4, 12))
        lbl(form, "Items:").pack(side="left")
        self.menu_items = tk.StringVar()
        ent(form, self.menu_items, 28).pack(side="left", padx=(4, 12))
        tk.Button(form, text="Save", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._save_menu).pack(side="left", padx=2)
        tk.Button(form, text="Delete Selected", bg=RED, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._delete_menu).pack(side="left", padx=4)

    def _load_menu_tree(self):
        self.menu_tree.delete(*self.menu_tree.get_children())
        rows = db.get_menu_for_week(self.menu_week_start.get())
        for row in rows:
            self.menu_tree.insert("", "end", iid=str(row["id"]),
                                  values=(row["id"], row["day_of_week"],
                                          row["meal_type"], row["items"]))
        if not rows:
            self.menu_tree.insert("", "end", values=("-","No entries","",""))

    def _save_menu(self):
        db.upsert_menu(self.menu_week_start.get(), self.menu_day.get(),
                       self.menu_meal.get(), self.menu_items.get())
        messagebox.showinfo("Saved", "Menu entry saved.")
        self._load_menu_tree()

    def _delete_menu(self):
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a row first.")
            return
        db.delete_menu_entry(int(sel[0]))
        messagebox.showinfo("Deleted", "Menu entry deleted.")
        self._load_menu_tree()

    # ── Users ──────────────────────────────────────────────────
    def _tab_users(self, parent):
        tk.Label(parent, text="User Management", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        self.user_tree = make_tree(parent,
                                    columns=("ID","Username","Role","Full Name","Email"),
                                    col_widths=[50, 130, 90, 180, 200], height=8)
        self._load_user_tree()

        add_frame = tk.LabelFrame(parent, text=" Add New User ",
                                   bg=CARD, fg=HIGHLIGHT, font=(FONT, 9, "bold"))
        add_frame.pack(fill="x", padx=12, pady=6)

        row1 = tk.Frame(add_frame, bg=CARD); row1.pack(fill="x", padx=8, pady=4)
        lbl(row1, "Username:").pack(side="left")
        self.add_uname = tk.StringVar()
        ent(row1, self.add_uname).pack(side="left", padx=(4, 16))
        lbl(row1, "Password:").pack(side="left")
        self.add_pwd = tk.StringVar()
        ent(row1, self.add_pwd).pack(side="left", padx=(4, 16))
        lbl(row1, "Role:").pack(side="left")
        self.add_role = tk.StringVar(value="student")
        ttk.Combobox(row1, textvariable=self.add_role,
                     values=["student", "staff"], state="readonly", width=10).pack(side="left", padx=(4, 0))

        row2 = tk.Frame(add_frame, bg=CARD); row2.pack(fill="x", padx=8, pady=4)
        lbl(row2, "Full Name:").pack(side="left")
        self.add_name = tk.StringVar()
        ent(row2, self.add_name, 24).pack(side="left", padx=(4, 16))
        lbl(row2, "Email:").pack(side="left")
        self.add_email = tk.StringVar()
        ent(row2, self.add_email, 24).pack(side="left", padx=(4, 16))
        tk.Button(row2, text="Add User", bg=ACCENT, fg=TEXT, bd=0, padx=12, pady=5,
                  cursor="hand2", command=self._add_user).pack(side="left")

        actions = tk.Frame(parent, bg=CARD)
        actions.pack(fill="x", padx=12, pady=4)
        tk.Button(actions, text="Delete Selected User", bg=RED, fg=TEXT, bd=0, padx=12, pady=6,
                  cursor="hand2", command=self._delete_user).pack(side="left", padx=4)
        lbl(actions, "New Password:").pack(side="left", padx=(20, 4))
        self.reset_pwd = tk.StringVar()
        ent(actions, self.reset_pwd, 16).pack(side="left", padx=(0, 6))
        tk.Button(actions, text="Reset Password", bg=BLUE, fg=TEXT, bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._reset_pwd).pack(side="left")

        fp_frame = tk.LabelFrame(parent, text=" Forgot Password Requests ",
                                  bg=CARD, fg=RED, font=(FONT, 9, "bold"))
        fp_frame.pack(fill="x", padx=12, pady=6)
        self.fp_tree = make_tree(fp_frame,
                                  columns=("Req ID","User ID","Username","Name","Role","Requested At"),
                                  col_widths=[70, 70, 120, 160, 90, 160], height=4)
        self._load_fp_tree()
        tk.Button(fp_frame, text="Resolve Selected", bg=ACCENT, fg=TEXT, bd=0,
                  padx=10, pady=5, cursor="hand2",
                  command=self._resolve_fp).pack(anchor="w", padx=8, pady=4)

    def _load_user_tree(self):
        self.user_tree.delete(*self.user_tree.get_children())
        for user in db.get_all_users():
            self.user_tree.insert("", "end", iid=str(user["id"]),
                                  values=(user["id"], user["username"], user["role"],
                                          user["full_name"] or "-", user["email"] or "-"))

    def _add_user(self):
        try:
            db.add_user(self.add_uname.get(), self.add_pwd.get(), self.add_role.get(),
                        self.add_name.get(), self.add_email.get())
            messagebox.showinfo("Added", f"User '{self.add_uname.get()}' added.")
            for v in (self.add_uname, self.add_pwd, self.add_name, self.add_email):
                v.set("")
            self._load_user_tree()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _delete_user(self):
        sel = self.user_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a user."); return
        uid = int(sel[0])
        if uid == self.user["id"]:
            messagebox.showerror("Error", "Cannot delete your own account."); return
        if messagebox.askyesno("Confirm", f"Delete user ID {uid}?"):
            db.delete_user(uid)
            messagebox.showinfo("Deleted", "User deleted.")
            self._load_user_tree()

    def _reset_pwd(self):
        sel = self.user_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a user."); return
        uid     = int(sel[0])
        new_pwd = self.reset_pwd.get().strip()
        if not new_pwd: messagebox.showinfo("Empty", "Enter a new password."); return
        db.reset_password(uid, new_pwd)
        messagebox.showinfo("Done", f"Password reset for user ID {uid}.")
        self.reset_pwd.set("")

    def _load_fp_tree(self):
        self.fp_tree.delete(*self.fp_tree.get_children())
        requests = db.get_forgot_password_requests()
        for r in requests:
            self.fp_tree.insert("", "end", iid=str(r["id"]),
                                values=(r["id"], r["user_id"], r["username"],
                                        r["full_name"] or "-", r["role"],
                                        str(r["requested_at"])[:16]))
        if not requests:
            self.fp_tree.insert("", "end", values=("-","No pending requests","","","",""))

    def _resolve_fp(self):
        sel = self.fp_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a request."); return
        db.resolve_forgot_password(int(sel[0]))
        messagebox.showinfo("Resolved", "Request marked resolved. Reset password above.")
        self._load_fp_tree()

    # ── Salary ─────────────────────────────────────────────────
    def _tab_salary(self, parent):
        tk.Label(parent, text="Salary Management", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.salary_tree = make_tree(parent,
                                      columns=("ID","Name","Role","Month","Year","Amount (Rs)","Status","Paid Date"),
                                      col_widths=[50,160,90,100,70,110,90,120], height=10)
        self._load_salary_tree()

        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=12, pady=6)
        lbl(form, "User ID:").pack(side="left")
        self.sal_uid = tk.StringVar()
        ent(form, self.sal_uid, 6).pack(side="left", padx=(4, 12))
        lbl(form, "Month (1-12):").pack(side="left")
        self.sal_month = tk.StringVar(value=str(date.today().month))
        ent(form, self.sal_month, 4).pack(side="left", padx=(4, 12))
        lbl(form, "Year:").pack(side="left")
        self.sal_year = tk.StringVar(value=str(date.today().year))
        ent(form, self.sal_year, 6).pack(side="left", padx=(4, 12))
        lbl(form, "Amount:").pack(side="left")
        self.sal_amt = tk.StringVar()
        ent(form, self.sal_amt, 10).pack(side="left", padx=(4, 12))
        tk.Button(form, text="Add / Update", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._add_salary).pack(side="left", padx=2)
        tk.Button(form, text="Mark Paid", bg=ACCENT2, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._pay_salary).pack(side="left", padx=4)

    def _load_salary_tree(self):
        self.salary_tree.delete(*self.salary_tree.get_children())
        for row in db.get_salary():
            self.salary_tree.insert("", "end", iid=str(row["id"]), values=(
                row["id"], row["full_name"], row["role"],
                MONTHS[row["month"] - 1], row["year"],
                f"Rs {row['amount']:.2f}", row["status"].capitalize(),
                str(row["paid_date"]) if row["paid_date"] else "-",
            ))

    def _add_salary(self):
        try:
            db.add_salary(int(self.sal_uid.get()), int(self.sal_month.get()),
                          int(self.sal_year.get()), float(self.sal_amt.get()))
            messagebox.showinfo("Saved", "Salary record saved.")
            self._load_salary_tree()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _pay_salary(self):
        sel = self.salary_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a record."); return
        db.pay_salary(int(sel[0]))
        messagebox.showinfo("Done", "Marked as paid.")
        self._load_salary_tree()

    # ── Mess Bills ─────────────────────────────────────────────
    def _tab_mess_bills(self, parent):
        tk.Label(parent, text="Mess Bill Management", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
                 
        tk.Label(parent, 
                 text="Auto-calculated dynamic mess bills for all students. Bills factor in missed days.\n"
                      "Fines (Rs 10/day) are applied automatically on pending bills past the 5th of the month.\n"
                      "Students initiate payments in their portal, which appear as 'Processing' until verified here.",
                 bg=CARD, fg=MUTED, font=(FONT, 9), justify="left").pack(anchor="w", padx=12, pady=(0, 4))

        self.bill_tree = make_tree(parent,
                                      columns=("ID","Student","Month","Year","Amount (Rs)","Fine (Rs)","Due","Status"),
                                      col_widths=[50,140,80,60,100,80,90,90], height=12)
        self._load_bill_tree()

        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=12, pady=6)
        tk.Button(form, text="Verify / Mark as Paid", bg=ACCENT2, fg=TEXT, bd=0, padx=14, pady=6,
                  cursor="hand2", command=self._pay_mess_bill).pack(side="left")
        tk.Button(form, text="Refresh Bills", bg=SIDEBAR, fg=MUTED, bd=0, padx=14, pady=6,
                  cursor="hand2", command=self._load_bill_tree).pack(side="left", padx=10)

    def _load_bill_tree(self):
        self.bill_tree.delete(*self.bill_tree.get_children())
        for row in db.get_mess_bills():
            month_name = date(row["year"], row["month"], 1).strftime("%b %Y")
            self.bill_tree.insert("", "end", iid=str(row["id"]), values=(
                row["id"], row["full_name"], month_name, row["year"],
                f"Rs {row['amount']:.2f}",
                f"Rs {row['fine']:.2f}",
                str(row["due_date"]),
                row["status"].capitalize()
            ))

    def _pay_mess_bill(self):
        sel = self.bill_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a bill."); return
        db.pay_mess_bill(int(sel[0]))
        messagebox.showinfo("Verified", "Bill successfully verified and marked as Paid.")
        self._load_bill_tree()

    # ── Inventory (admin: full add/delete/update) ───────────────
    def _tab_inventory(self, parent):
        tk.Label(parent, text="Inventory Management", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.inv_tree = make_tree(parent,
                                   columns=("ID","Item","Quantity","Unit","Last Updated"),
                                   col_widths=[60, 180, 100, 80, 160], height=10)
        self._load_inv_tree()

        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=12, pady=6)
        lbl(form, "Item Name:").pack(side="left")
        self.inv_item = tk.StringVar()
        ent(form, self.inv_item, 20).pack(side="left", padx=(4, 12))
        lbl(form, "Quantity:").pack(side="left")
        self.inv_qty  = tk.StringVar()
        ent(form, self.inv_qty, 8).pack(side="left", padx=(4, 12))
        lbl(form, "Unit:").pack(side="left")
        self.inv_unit = tk.StringVar(value="kg")
        ttk.Combobox(form, textvariable=self.inv_unit,
                     values=["kg", "L", "pcs", "g", "ml", "dozen"],
                     state="readonly", width=8).pack(side="left", padx=(4, 12))
        tk.Button(form, text="Save / Update", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._save_inv).pack(side="left", padx=2)
        tk.Button(form, text="Delete Selected", bg=RED, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._delete_inv).pack(side="left", padx=4)

        # Usage log section
        tk.Label(parent, text="Staff Usage Log:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.usage_log_tree = make_tree(parent,
                                         columns=("Date","Staff","Item","Qty Used","Unit","Note"),
                                         col_widths=[110, 140, 160, 90, 70, 200], height=6)
        self._load_usage_log()

    def _load_inv_tree(self):
        self.inv_tree.delete(*self.inv_tree.get_children())
        for item in db.get_inventory():
            self.inv_tree.insert("", "end", iid=str(item["id"]),
                                 values=(item["id"], item["item_name"],
                                         item["quantity"], item["unit"] or "-",
                                         str(item["updated_at"])[:16]))
        if not db.get_inventory():
            self.inv_tree.insert("", "end", values=("-","No items","","",""))

    def _save_inv(self):
        try:
            db.upsert_inventory(self.inv_item.get().strip(), float(self.inv_qty.get()), self.inv_unit.get())
            messagebox.showinfo("Saved", "Inventory updated.")
            self._load_inv_tree()
            self._load_usage_log()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _delete_inv(self):
        sel = self.inv_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select an item."); return
        db.delete_inventory_item(int(sel[0]))
        messagebox.showinfo("Deleted", "Item removed.")
        self._load_inv_tree()

    def _load_usage_log(self):
        self.usage_log_tree.delete(*self.usage_log_tree.get_children())
        records = db.get_inventory_usage(
            from_date=date.today() - timedelta(days=30),
            to_date=date.today()
        )
        for row in records:
            self.usage_log_tree.insert("", "end", values=(
                str(row["usage_date"]), row["staff_name"], row["item_name"],
                row["used_qty"], row["unit"] or "-", row["note"] or "",
            ))
        if not records:
            self.usage_log_tree.insert("", "end", values=("-","No usage records","","","",""))

    # ── Food Waste ─────────────────────────────────────────────
    def _tab_foodwaste(self, parent):
        tk.Label(parent, text="Food Waste Report", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "From:").pack(side="left")
        self.fw_from = tk.StringVar(value=str(date.today() - timedelta(days=30)))
        ent(ctrl, self.fw_from, 12).pack(side="left", padx=(4, 12))
        lbl(ctrl, "To:").pack(side="left")
        self.fw_to   = tk.StringVar(value=str(date.today()))
        ent(ctrl, self.fw_to, 12).pack(side="left", padx=(4, 12))
        tk.Button(ctrl, text="Filter", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_fw_tree).pack(side="left")

        self.fw_tree = make_tree(parent,
                                  columns=("Date","Staff Name","Item","Quantity","Unit"),
                                  col_widths=[110, 160, 160, 100, 80], height=14)
        self._load_fw_tree()

    def _load_fw_tree(self):
        self.fw_tree.delete(*self.fw_tree.get_children())
        records = db.get_food_waste(from_date=self.fw_from.get(), to_date=self.fw_to.get())
        for row in records:
            self.fw_tree.insert("", "end", values=(
                str(row["waste_date"]), row["full_name"],
                row["item_name"], row["quantity"], row["unit"] or "-",
            ))
        if not records:
            self.fw_tree.insert("", "end", values=("No records","","","",""))

    # ── Poll Data ──────────────────────────────────────────────
    def _tab_polldata(self, parent):
        self._pol_parent = parent
        self._render_polldata()

    def _render_polldata(self):
        parent = self._pol_parent
        for w in parent.winfo_children():
            w.destroy()

        today    = date.today()
        tomorrow = today + timedelta(days=1)

        tk.Label(parent, text="Student Poll Data — Meal-wise Headcounts",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(parent,
                 text="'Today' shows what students voted for yesterday (what kitchen should prepare today).  "
                      "'Tomorrow' is the live active poll.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        wrapper   = tk.Frame(parent, bg=CARD)
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
                        f"Today's Poll — {today.strftime('%A, %d %b %Y')}")
        draw_poll_chart(inner, tomorrow,
                        f"Tomorrow's Live Poll — {tomorrow.strftime('%A, %d %b %Y')}")

        tk.Button(parent, text="🔄 Refresh", bg=ACCENT, fg=TEXT, bd=0, padx=12, pady=5,
                  cursor="hand2", command=self._render_polldata).pack(anchor="w", padx=12, pady=6)

    # ── Feedback ───────────────────────────────────────────────
    def _tab_feedback(self, parent):
        tk.Label(parent, text="Student Feedback Overview", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        avg   = db.get_avg_rating()
        dist  = db.get_rating_distribution()
        total = sum(dist.values())

        # Summary banner
        banner = tk.Frame(parent, bg=SIDEBAR)
        banner.pack(fill="x", padx=12, pady=6)
        tk.Label(banner, text=f"⭐  Average Rating: {avg:.1f} / 5.0",
                 bg=SIDEBAR, fg=GOLD, font=(FONT, 16, "bold")).pack(side="left", padx=16, pady=12)
        tk.Label(banner, text=f"Total feedback submissions: {total}",
                 bg=SIDEBAR, fg=MUTED, font=(FONT, 10)).pack(side="left", padx=8)

        # Distribution chart
        dist_frame = tk.Frame(parent, bg=CARD)
        dist_frame.pack(fill="x", padx=12, pady=4)
        tk.Label(dist_frame, text="Rating Distribution:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", pady=(0, 4))
        for star in range(5, 0, -1):
            cnt  = dist[star]
            row  = tk.Frame(dist_frame, bg=CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{'★'*star}{'☆'*(5-star)}", bg=CARD, fg=GOLD,
                     font=(FONT, 10), width=12, anchor="w").pack(side="left")
            bar_w = int((cnt / max(total, 1)) * 240)
            tk.Frame(row, bg=ACCENT2, width=bar_w, height=16).pack(side="left")
            tk.Label(row, text=f"  {cnt} reviews", bg=CARD, fg=MUTED,
                     font=(FONT, 9)).pack(side="left")

        # Full table
        tk.Label(parent, text="All Feedback Entries:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(12, 2))
        tree = make_tree(parent,
                         columns=("Date","Student","Rating","Comment"),
                         col_widths=[110, 160, 80, 380])
        for row in db.get_all_feedback():
            stars = "★" * row["rating"] + "☆" * (5 - row["rating"])
            tree.insert("", "end", values=(
                str(row["created_at"])[:10],
                row["full_name"] or row["username"],
                stars, (row["comment"] or "")[:100],
            ))

    # ── Demand Prediction ──────────────────────────────────────
    def _tab_demand(self, parent):
        self._demand_parent = parent
        tk.Label(parent, text="Demand Prediction", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

        # Algorithm explanation box
        info = tk.Frame(parent, bg="#0d2a1a", bd=0)
        info.pack(fill="x", padx=12, pady=(0, 8))
        info_text = (
            "Algorithm: Rule-based text parsing. Detects dish types (e.g., Biryani, Dosa, Rice, Snacks) "
            "from the menu and applies real-world piece/gram/liter formulas per predicted student to "
            "calculate exact demand for raw materials."
        )
        tk.Label(info, text=info_text, bg="#0d2a1a", fg="#86efac", font=(FONT, 8),
                 wraplength=780, justify="left").pack(padx=12, pady=8)

        # Target date picker
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "Predict for date:").pack(side="left")
        tomorrow = date.today() + timedelta(days=1)
        self.pred_date = tk.StringVar(value=str(tomorrow))
        ent(ctrl, self.pred_date, 14).pack(side="left", padx=(4, 12))
        tk.Button(ctrl, text="Calculate Prediction", bg=ACCENT, fg=TEXT,
                  bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._run_prediction).pack(side="left")

        # Results area (recreated on each run)
        self._demand_result_frame = tk.Frame(parent, bg=CARD)
        self._demand_result_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self._show_demand_placeholder()

    def _show_demand_placeholder(self):
        for w in self._demand_result_frame.winfo_children():
            w.destroy()
        tk.Label(self._demand_result_frame,
                 text="Click 'Calculate Prediction' to see results.",
                 bg=CARD, fg=MUTED, font=(FONT, 10)).pack(pady=20)

    def _run_prediction(self):
        try:
            target = date.fromisoformat(self.pred_date.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Date", "Enter date as YYYY-MM-DD.")
            return

        results = db.get_demand_prediction(target)

        for w in self._demand_result_frame.winfo_children():
            w.destroy()

        tk.Label(self._demand_result_frame,
                 text=f"Prediction for {target.strftime('%A, %d %b %Y')}",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))

        # Summary cards
        cards_row = tk.Frame(self._demand_result_frame, bg=CARD)
        cards_row.pack(fill="x", pady=4)
        for res in results:
            card = tk.Frame(cards_row, bg=SIDEBAR, padx=16, pady=10)
            card.pack(side="left", padx=8, fill="y")
            color = MEAL_COLORS.get(res["meal"], ACCENT)
            tk.Label(card, text=res["meal"], bg=SIDEBAR, fg=color,
                     font=(FONT, 10, "bold")).pack()
            tk.Label(card, text=str(res["predicted_students"]),
                     bg=SIDEBAR, fg=TEXT, font=(FONT, 22, "bold")).pack()
            tk.Label(card, text="students", bg=SIDEBAR, fg=MUTED, font=(FONT, 8)).pack()
            tk.Label(card, text=f"≈ {res['recommended_qty']} {res['unit']}",
                     bg=SIDEBAR, fg=HIGHLIGHT, font=(FONT, 10)).pack(pady=(4, 0))

        # Detailed table
        tk.Label(self._demand_result_frame, text="Detailed Breakdown:",
                 bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", pady=(14, 2))
        tree = make_tree(self._demand_result_frame,
                         columns=("Meal","Item","Predicted","Recommended","Last Prep Date"),
                         col_widths=[90, 220, 100, 140, 120], height=5)
        for res in results:
            tree.insert("", "end", values=(
                res["meal"], res["items"][:24] + ("..." if len(res["items"]) > 24 else ""),
                res["predicted_students"],
                f"{res['recommended_qty']} {res['unit']}",
                str(res["based_on_date"]) if res["based_on_date"] else "No history"
            ))

        # Canvas bar chart
        tk.Label(self._demand_result_frame, text="Headcount Bar Chart:",
                 bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", pady=(10, 2))
        chart_frame = tk.Frame(self._demand_result_frame, bg=SIDEBAR)
        chart_frame.pack(fill="x", padx=4, pady=4)
        max_val = max((r["predicted_students"] for r in results), default=1) or 1
        for res in results:
            row = tk.Frame(chart_frame, bg=SIDEBAR)
            row.pack(fill="x", padx=12, pady=4)
            color = MEAL_COLORS.get(res["meal"], ACCENT)
            tk.Label(row, text=res["meal"], bg=SIDEBAR, fg=TEXT,
                     font=(FONT, 9, "bold"), width=12, anchor="w").pack(side="left")
            bar_w = int((res["predicted_students"] / max_val) * 320)
            tk.Frame(row, bg=color, width=bar_w, height=22).pack(side="left")
            tk.Label(row, text=f"  {res['predicted_students']} students  |  {res['recommended_qty']} {res['unit']}",
                     bg=SIDEBAR, fg=MUTED, font=(FONT, 9)).pack(side="left")

    # ── Food Prepared (admin view all staff) ───────────────────
    def _tab_food_prepared(self, parent):
        tk.Label(parent, text="Food Prepared Log (All Staff)",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "From:").pack(side="left")
        self.fpl_from = tk.StringVar(value=str(date.today() - timedelta(days=30)))
        ent(ctrl, self.fpl_from, 12).pack(side="left", padx=(4, 12))
        lbl(ctrl, "To:").pack(side="left")
        self.fpl_to   = tk.StringVar(value=str(date.today()))
        ent(ctrl, self.fpl_to, 12).pack(side="left", padx=(4, 12))
        tk.Button(ctrl, text="Filter", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_fpl_tree).pack(side="left")

        self.fpl_tree = make_tree(parent,
                                   columns=("Date","Staff","Meal","Item","Qty Made","Unit","Servings"),
                                   col_widths=[110, 140, 100, 160, 90, 70, 90], height=16)
        self._load_fpl_tree()

    def _load_fpl_tree(self):
        self.fpl_tree.delete(*self.fpl_tree.get_children())
        records = db.get_food_prepared(from_date=self.fpl_from.get(), to_date=self.fpl_to.get())
        for row in records:
            self.fpl_tree.insert("", "end", values=(
                str(row["prep_date"]), row["full_name"], row["meal_type"],
                row["item_name"], row["quantity_made"],
                row["unit"] or "-", row["servings"],
            ))
        if not records:
            self.fpl_tree.insert("", "end", values=("-","No records","","","","",""))

    # ── Complaints ─────────────────────────────────────────────
    def _tab_complaints(self, parent):
        tk.Label(parent, text="Complaints & Suggestions", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.comp_tree = make_tree(parent,
                                    columns=("ID","User","Role","Date","Message","Status"),
                                    col_widths=[50, 140, 90, 110, 340, 100], height=12)
        self._load_comp_tree()
        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=12, pady=6)
        lbl(form, "Update Status:").pack(side="left")
        self.comp_status = tk.StringVar(value="reviewed")
        ttk.Combobox(form, textvariable=self.comp_status,
                     values=["open", "reviewed", "closed"],
                     state="readonly", width=10).pack(side="left", padx=(4, 12))
        tk.Button(form, text="Update Selected", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._update_comp).pack(side="left")

    def _load_comp_tree(self):
        self.comp_tree.delete(*self.comp_tree.get_children())
        for c in db.get_complaints():
            self.comp_tree.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c["full_name"], c.get("role", "-"),
                str(c["created_at"])[:10],
                c["message"][:80] + ("..." if len(c["message"]) > 80 else ""),
                c["status"].capitalize(),
            ))
        if not db.get_complaints():
            self.comp_tree.insert("", "end", values=("-","No complaints","","","",""))

    def _update_comp(self):
        sel = self.comp_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a complaint."); return
        db.update_complaint_status(int(sel[0]), self.comp_status.get())
        messagebox.showinfo("Updated", "Status updated.")
        self._load_comp_tree()

    # ── Notifications ──────────────────────────────────────────
    def _tab_notifications(self, parent):
        tk.Label(parent, text="Send Notification", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=12, pady=6)
        lbl(form, "Send to:").pack(side="left")
        self.notif_role = tk.StringVar(value="student")
        ttk.Combobox(form, textvariable=self.notif_role,
                     values=["student", "staff", "all"],
                     state="readonly", width=10).pack(side="left", padx=(4, 12))
        lbl(form, "Title:").pack(side="left")
        self.notif_title = tk.StringVar()
        ent(form, self.notif_title, 24).pack(side="left", padx=(4, 0))

        msg_frame = tk.Frame(parent, bg=CARD)
        msg_frame.pack(fill="x", padx=12, pady=4)
        lbl(msg_frame, "Message:").pack(anchor="w")
        self.notif_msg = scrolledtext.ScrolledText(msg_frame, bg=SIDEBAR, fg=TEXT,
                                                    font=(FONT, 10), wrap="word",
                                                    height=5, relief="flat")
        self.notif_msg.pack(fill="x")
        tk.Button(parent, text="Send Notification", bg=ACCENT, fg=TEXT, bd=0,
                  padx=14, pady=6, cursor="hand2",
                  command=self._send_notif).pack(anchor="w", padx=12, pady=6)

        lbl(parent, "Sent Notifications:", fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(6, 2))
        self.notif_tree = make_tree(parent,
                                     columns=("ID","Target","Title","Sent At"),
                                     col_widths=[50, 90, 300, 160], height=6)
        self._load_notif_tree()

    def _send_notif(self):
        title = self.notif_title.get().strip()
        msg   = self.notif_msg.get("1.0", "end").strip()
        if not title or not msg:
            messagebox.showinfo("Empty", "Enter title and message.")
            return
        db.send_notification(title, msg, self.notif_role.get())
        messagebox.showinfo("Sent", "Notification sent successfully.")
        self.notif_title.set("")
        self.notif_msg.delete("1.0", "end")
        self._load_notif_tree()

    def _load_notif_tree(self):
        self.notif_tree.delete(*self.notif_tree.get_children())
        for n in db.get_all_notifications():
            self.notif_tree.insert("", "end", values=(
                n["id"], n["target_role"].capitalize(), n["title"],
                str(n["created_at"])[:16],
            ))

    # ── Manual ─────────────────────────────────────────────────
    def _tab_manual(self, parent):
        tk.Label(parent, text="Edit User Manuals", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "Edit manual for:").pack(side="left")
        self.manual_role = tk.StringVar(value="student")
        ttk.Combobox(ctrl, textvariable=self.manual_role,
                     values=["student", "staff", "admin"],
                     state="readonly", width=10).pack(side="left", padx=(4, 12))
        tk.Button(ctrl, text="Load", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_manual_editor).pack(side="left", padx=2)
        tk.Button(ctrl, text="Save", bg=ACCENT2, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._save_manual).pack(side="left", padx=4)
        self.manual_txt = scrolledtext.ScrolledText(parent, bg=SIDEBAR, fg=TEXT,
                                                     font=(FONT, 10), wrap="word",
                                                     relief="flat", bd=0)
        self.manual_txt.pack(fill="both", expand=True, padx=12, pady=8)
        self._load_manual_editor()

    def _load_manual_editor(self):
        self.manual_txt.delete("1.0", "end")
        self.manual_txt.insert("1.0", db.get_manual(self.manual_role.get()))

    def _save_manual(self):
        db.update_manual(self.manual_role.get(), self.manual_txt.get("1.0", "end").strip())
        messagebox.showinfo("Saved", "User manual updated.")

    # ── Customer Orders (Private Kitchen only) ──────────────────
    def _tab_customer_orders(self, parent):
        tk.Label(parent, text="Customer Orders — Today's Queue",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(parent, text="Manage walk-in and pre-orders. Select an order and update its status.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        # Status filter
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "Filter status:").pack(side="left")
        self.co_status_filter = tk.StringVar(value="all")
        ttk.Combobox(ctrl, textvariable=self.co_status_filter,
                     values=["all", "placed", "preparing", "ready_for_pickup", "completed", "cancelled"],
                     state="readonly", width=18).pack(side="left", padx=6)
        tk.Button(ctrl, text="Refresh", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_customer_orders).pack(side="left", padx=4)

        self.co_tree = make_tree(parent,
            columns=("ID", "Token", "Customer", "Phone", "Items", "Total (₹)", "Status", "Time"),
            col_widths=[50, 80, 130, 100, 200, 90, 120, 120], height=10)

        # Status update bar
        upd = tk.Frame(parent, bg=CARD)
        upd.pack(fill="x", padx=12, pady=6)
        lbl(upd, "Update selected order to:").pack(side="left")
        self.co_new_status = tk.StringVar(value="preparing")
        ttk.Combobox(upd, textvariable=self.co_new_status,
                     values=["preparing", "ready_for_pickup", "completed", "cancelled"],
                     state="readonly", width=16).pack(side="left", padx=6)
        tk.Button(upd, text="✔ Update Status", bg=ACCENT2, fg=TEXT, bd=0, padx=12, pady=4,
                  cursor="hand2", command=self._update_customer_order_status).pack(side="left", padx=4)

        self._load_customer_orders()

    def _load_customer_orders(self):
        self.co_tree.delete(*self.co_tree.get_children())
        sf = self.co_status_filter.get()
        orders = db.get_customer_orders(
            kitchen_user_id=self.user["id"],
            status=None if sf == "all" else sf
        )
        for o in orders:
            try:
                import json
                items = json.loads(o["items_json"].replace("'", '"'))
                item_str = ", ".join(f"{it.get('name','?')}×{it.get('qty',1)}" for it in items)
            except Exception:
                item_str = str(o["items_json"])[:60]
            self.co_tree.insert("", "end", iid=str(o["id"]), values=(
                o["id"], o["pickup_token"], o["customer_name"], o["customer_phone"],
                item_str, f"₹{float(o['total_amount']):.2f}",
                o["order_status"].replace("_"," ").title(),
                str(o["ordered_at"])[:16]
            ))

    def _update_customer_order_status(self):
        sel = self.co_tree.selection()
        if not sel:
            messagebox.showwarning("Select Order", "Please select an order first.")
            return
        oid = int(sel[0])
        new_st = self.co_new_status.get()
        db.update_customer_order_status(oid, new_st)
        messagebox.showinfo("Updated", f"Order #{oid} marked as '{new_st.replace('_',' ')}'.")
        self._load_customer_orders()

    # ── Order Summary (Private Kitchen only) ───────────────────
    def _tab_order_summary(self, parent):
        from datetime import date
        tk.Label(parent, text="Daily Order Summary",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "Date:").pack(side="left")
        self.os_date = tk.StringVar(value=str(date.today()))
        ent(ctrl, self.os_date, 14).pack(side="left", padx=6)
        tk.Button(ctrl, text="Load", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._load_order_summary).pack(side="left", padx=4)

        self.os_summary_frame = tk.Frame(parent, bg=CARD)
        self.os_summary_frame.pack(fill="x", padx=16, pady=8)
        self._load_order_summary()

    def _load_order_summary(self):
        for w in self.os_summary_frame.winfo_children():
            w.destroy()
        try:
            from datetime import date as dt_date
            d = dt_date.fromisoformat(self.os_date.get().strip())
        except Exception:
            d = date.today()
        s = db.get_customer_order_summary(self.user["id"], for_date=d)

        stats = [
            ("📦 Total Orders",     s["total_orders"]),
            ("✅ Completed",         s["completed"]),
            ("⏳ Active",            s["active"]),
            ("❌ Cancelled",         s["cancelled"]),
            ("💰 Revenue",           f"₹{float(s['total_revenue']):.2f}"),
        ]
        for i, (label, val) in enumerate(stats):
            card = tk.Frame(self.os_summary_frame, bg="#132030", padx=18, pady=12)
            card.grid(row=0, column=i, padx=8, pady=4, sticky="nsew")
            tk.Label(card, text=str(val), bg="#132030", fg=HIGHLIGHT,
                     font=(FONT, 18, "bold")).pack()
            tk.Label(card, text=label, bg="#132030", fg=MUTED,
                     font=(FONT, 9)).pack()

    # ── Post Surplus (all admins) ───────────────────────────────
    def _tab_post_surplus(self, parent):
        from datetime import datetime, timedelta
        tk.Label(parent, text="Post Surplus Food Listing",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(parent,
                 text="List safe surplus food — donate free to NGOs or sell at a discounted rate to community buyers.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 8))

        form = tk.LabelFrame(parent, text=" Listing Details ", bg=CARD, fg=HIGHLIGHT,
                             font=(FONT, 10, "bold"), padx=14, pady=10)
        form.pack(fill="x", padx=12, pady=4)

        def row(lbl_text, var, width=28):
            r = tk.Frame(form, bg=CARD)
            r.pack(fill="x", pady=3)
            lbl(r, lbl_text, width=18, anchor="w").pack(side="left")
            e = ent(r, var, width)
            e.pack(side="left")
            return e

        self.ps_item = tk.StringVar(value="Vegetable Pulao")
        self.ps_qty  = tk.StringVar(value="10")
        self.ps_unit = tk.StringVar(value="kg")
        self.ps_loc  = tk.StringVar(value="Campus Main Block")
        self.ps_lat  = tk.StringVar(value="12.9716")
        self.ps_lon  = tk.StringVar(value="77.5946")
        self.ps_hrs  = tk.StringVar(value="4")

        row("Food Item Name:", self.ps_item)
        row("Quantity:", self.ps_qty, 10)
        row("Unit (kg/servings):", self.ps_unit, 12)
        row("Location Address:", self.ps_loc)
        row("Latitude:", self.ps_lat, 14)
        row("Longitude:", self.ps_lon, 14)
        row("Safe Window (hours):", self.ps_hrs, 8)

        rc = tk.Frame(form, bg=CARD)
        rc.pack(fill="x", pady=4)
        lbl(rc, "Category:", width=18, anchor="w").pack(side="left")
        self.ps_cat = tk.StringVar(value="cooked_meal")
        ttk.Combobox(rc, textvariable=self.ps_cat,
                     values=["cooked_meal", "raw_produce", "packaged_fpu", "bakery"],
                     state="readonly", width=16).pack(side="left")

        rp = tk.Frame(form, bg=CARD)
        rp.pack(fill="x", pady=4)
        lbl(rp, "Price Type:", width=18, anchor="w").pack(side="left")
        self.ps_price_type = tk.StringVar(value="free")
        ttk.Combobox(rp, textvariable=self.ps_price_type,
                     values=["free", "discounted"],
                     state="readonly", width=12).pack(side="left", padx=(0,10))
        lbl(rp, "Discounted Price (₹/unit):").pack(side="left")
        self.ps_disc_price = tk.StringVar(value="0")
        ent(rp, self.ps_disc_price, 10).pack(side="left", padx=6)

        tk.Button(form, text="📤 Post Surplus Listing", bg=ACCENT, fg=TEXT,
                  font=(FONT, 9, "bold"), bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._submit_surplus).pack(anchor="w", pady=(10, 0))

        # Recent listings
        tk.Label(parent, text="Recent Surplus Listings:",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.ps_tree = make_tree(parent,
            columns=("Item", "Qty", "Category", "Price Type", "Status", "Expires"),
            col_widths=[180, 80, 110, 100, 100, 140], height=5)
        self._load_surplus_listings()

    def _submit_surplus(self):
        from datetime import datetime, timedelta
        try:
            qty  = float(self.ps_qty.get())
            hrs  = float(self.ps_hrs.get())
            lat  = float(self.ps_lat.get())
            lon  = float(self.ps_lon.get())
            disc = float(self.ps_disc_price.get())
        except ValueError:
            messagebox.showerror("Input Error", "Quantity, hours, lat/lon, and price must be numbers.")
            return
        expiry = datetime.now() + timedelta(hours=hrs)
        db.add_surplus_listing(
            seller_id=self.user["id"],
            item_name=self.ps_item.get().strip(),
            category=self.ps_cat.get(),
            total_quantity=qty,
            available_qty=qty,
            unit=self.ps_unit.get().strip() or "kg",
            expiry_datetime=expiry,
            price_type=self.ps_price_type.get(),
            location_address=self.ps_loc.get().strip(),
            latitude=lat, longitude=lon,
            original_price=disc, discounted_price=disc,
            quality_status="verified_fresh", quality_score=5
        )
        messagebox.showinfo("Posted", f"Surplus listing for '{self.ps_item.get()}' posted successfully!")
        self._load_surplus_listings()

    def _load_surplus_listings(self):
        self.ps_tree.delete(*self.ps_tree.get_children())
        listings = db.get_kitchen_listings(self.user["id"])
        for l in listings:
            exp = str(l.get("expiry_datetime", ""))[:16]
            self.ps_tree.insert("", "end", values=(
                l["item_name"], f"{float(l['available_qty']):.1f} {l['unit']}",
                l["category"], l["price_type"], l["status"], exp
            ))

    # ── Monthly ESG Report (all admins) ────────────────────────
    def _tab_monthly_report(self, parent):
        tk.Label(parent, text="Monthly ESG Impact Report",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(parent,
                 text="View food preparation, waste reduction, surplus redistribution, and carbon offset for any month.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 6))

        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=12, pady=4)
        lbl(ctrl, "Year:").pack(side="left")
        self.mr_year  = tk.StringVar(value=str(date.today().year))
        ent(ctrl, self.mr_year, 6).pack(side="left", padx=4)
        lbl(ctrl, "Month:").pack(side="left", padx=(10, 0))
        self.mr_month = tk.StringVar(value=str(date.today().month))
        ttk.Combobox(ctrl, textvariable=self.mr_month,
                     values=[str(i) for i in range(1, 13)],
                     state="readonly", width=4).pack(side="left", padx=4)
        tk.Button(ctrl, text="Generate Report", bg=ACCENT, fg=TEXT, bd=0, padx=12, pady=4,
                  cursor="hand2", command=self._generate_monthly_report).pack(side="left", padx=8)

        self.mr_display = tk.Frame(parent, bg=CARD)
        self.mr_display.pack(fill="both", expand=True, padx=12, pady=8)
        self._generate_monthly_report()

    def _generate_monthly_report(self):
        for w in self.mr_display.winfo_children():
            w.destroy()
        try:
            yr = int(self.mr_year.get())
            mo = int(self.mr_month.get())
        except ValueError:
            messagebox.showerror("Input", "Enter valid year and month.")
            return

        r = db.get_monthly_kitchen_report(seller_id=self.user["id"], year=yr, month=mo)

        mname = MONTHS[r["month"] - 1] if 1 <= r["month"] <= 12 else str(r["month"])
        tk.Label(self.mr_display, text=f"Report: {mname} {r['year']}",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 13, "bold")).grid(row=0, column=0, columnspan=3, pady=(0,10), sticky="w")

        metrics = [
            ("🍳 Food Prepared",          f"{r['food_prepared_kg']} kg"),
            ("🍽 Estimated Consumption",   f"{r['estimated_consumption_kg']} kg"),
            ("🗑 Avoidable Waste",         f"{r['avoidable_waste_kg']} kg"),
            ("📦 Surplus Redistributed",  f"{r['surplus_redistributed_kg']} kg"),
            ("🎁 Free Donations",          f"{r['free_donations_kg']} kg"),
            ("🧑‍🤝‍🧑 Meals Provided",       str(r["meals_provided"])),
            ("💰 Revenue Recovered",       f"₹{r['revenue_recovered_inr']:.2f}"),
            ("💡 Cost Saved",              f"₹{r['cost_saved_inr']:.2f}"),
            ("⚡ Biogas Diverted",         f"{r['biogas_diverted_kg']} kg"),
            ("🌱 Farm Compost",            f"{r['farm_compost_kg']} kg"),
            ("🌍 CO₂ Avoided",             f"{r['co2_avoided_kg']} kg"),
            ("⭐ Eco-Points Earned",        str(r["eco_points_earned"])),
        ]
        for i, (label, val) in enumerate(metrics):
            col = i % 3
            rw  = (i // 3) + 1
            card = tk.Frame(self.mr_display, bg="#132030", padx=16, pady=10)
            card.grid(row=rw, column=col, padx=8, pady=5, sticky="nsew")
            tk.Label(card, text=label, bg="#132030", fg=MUTED, font=(FONT, 8)).pack(anchor="w")
            tk.Label(card, text=val, bg="#132030", fg=HIGHLIGHT, font=(FONT, 16, "bold")).pack(anchor="w")

