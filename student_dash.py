"""
student_dash.py - EcoMess Student Dashboard
Tabs: Menu | Fee | Poll | Feedback | Attendance | Notifications | Complaints | Manual
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import date, timedelta, datetime

import database as db

BG     = "#1b2228"
CARD   = "#1f3040"
SIDEBAR = "#0d1b2a"
ACCENT  = "#2d6a4f"
ACCENT2 = "#40916c"
HIGHLIGHT = "#74c69d"
TEXT   = "#edf2f4"
MUTED  = "#94a3b8"
STAR_ON  = "#f4d03f"
STAR_OFF = "#3d5166"
FONT   = "Segoe UI"

DAYS  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MEALS = ["Breakfast","Lunch","Snacks","Dinner"]


def get_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())


def make_tree(parent, columns, col_widths=None):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="both", expand=True, padx=8, pady=8)
    tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
    for i, col in enumerate(columns):
        width = col_widths[i] if col_widths else 120
        tree.heading(col, text=col)
        tree.column(col, width=width, minwidth=60, anchor="center")
    sb_y = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    sb_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side="right",  fill="y")
    sb_x.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    return tree


def make_scrollable_container(parent):
    wrapper  = tk.Frame(parent, bg=CARD)
    wrapper.pack(fill="both", expand=True, padx=8, pady=8)
    canvas   = tk.Canvas(wrapper, bg=CARD, highlightthickness=0)
    scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    container = tk.Frame(canvas, bg=CARD)
    wid = canvas.create_window((0, 0), window=container, anchor="nw")

    def sync_region(_e=None): canvas.configure(scrollregion=canvas.bbox("all"))
    def sync_width(e):        canvas.itemconfigure(wid, width=e.width)
    def on_wheel(e):
        if container.winfo_reqheight() > canvas.winfo_height():
            canvas.yview_scroll(int(-e.delta / 120), "units")

    container.bind("<Configure>", sync_region)
    canvas.bind("<Configure>",    sync_width)
    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", on_wheel))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
    return container


# ──────────────────────────────────────────────────────────────
#  Star Rating Widget
# ──────────────────────────────────────────────────────────────
class StarRating(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=CARD, **kwargs)
        self._rating = 0
        self._btns   = []
        for i in range(1, 6):
            btn = tk.Label(
                self, text="★", font=(FONT, 22), bg=CARD,
                fg=STAR_OFF, cursor="hand2"
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>",      lambda e, v=i: self._set(v))
            btn.bind("<Enter>",         lambda e, v=i: self._hover(v))
            btn.bind("<Leave>",         lambda e:      self._restore())
            self._btns.append(btn)

    def _set(self, val):
        self._rating = val
        self._restore()

    def _hover(self, val):
        for i, btn in enumerate(self._btns):
            btn.config(fg=STAR_ON if i < val else STAR_OFF)

    def _restore(self):
        for i, btn in enumerate(self._btns):
            btn.config(fg=STAR_ON if i < self._rating else STAR_OFF)

    def get(self):
        return self._rating

    def reset(self):
        self._rating = 0
        self._restore()


# ──────────────────────────────────────────────────────────────
#  Student Dashboard
# ──────────────────────────────────────────────────────────────
class StudentDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app  = app
        self.user = app.current_user
        self.inst_type = (self.user.get('institution_type') or 'general').lower()
        self.category  = db.get_kitchen_category(self.inst_type)
        self.configure(style="TFrame")
        self._build()
        self._schedule_midnight_reset()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        portal_name = "🎓 Institution Student & Resident Portal" if self.category == 'institutional' else "🍳 Private Kitchen Diner & Customer Portal"
        inst_label = self.inst_type.replace('_', ' ').title()
        tk.Label(
            header,
            text=f"{portal_name} ({inst_label}) — {self.user.get('full_name') or self.user['username']}",
            bg=ACCENT, fg=TEXT, font=(FONT, 12, "bold"),
        ).pack(side="left", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = [
            ("Menu",          self._tab_menu),
            ("Mess Bill",     self._tab_mess_bill),
            ("Poll",          self._tab_poll),
            ("Feedback",      self._tab_feedback),
            ("Complaints",    self._tab_complaints),
            ("Notifications", self._tab_notifications),
            ("User Manual",   self._tab_manual),
        ]
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
        tk.Label(ctrl, text="Weekly Menu", bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(side="left")
        tk.Label(ctrl, text=f"(Week of {week_start})", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side="left", padx=8)

        nav = tk.Frame(parent, bg=CARD)
        nav.pack(fill="x", padx=12, pady=4)
        tk.Button(nav, text="< Prev", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._menu_nav(-1)).pack(side="left")
        self.day_label = tk.Label(nav, text="", bg=CARD, fg=TEXT, font=(FONT, 11, "bold"), width=14)
        self.day_label.pack(side="left", padx=20)
        tk.Button(nav, text="Next >", bg=ACCENT, fg=TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._menu_nav(1)).pack(side="left")

        self.menu_card = tk.Frame(parent, bg=SIDEBAR, bd=1, relief="flat")
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
            row = tk.Frame(self.menu_card, bg=CARD)
            row.pack(fill="x", padx=16, pady=6)
            tk.Label(row, text=meal, bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold"),
                     width=10, anchor="w").pack(side="left", padx=8)
            tk.Label(row, text=entries[0]["items"] if entries else "-",
                     bg=CARD, fg=TEXT, font=(FONT, 10), anchor="w").pack(side="left", padx=8)

    # ── Mess Bill ────────────────────────────────────────────────────
    def _tab_mess_bill(self, parent):
        tk.Label(parent, text="Mess Bill", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
                 
        info_frame = tk.Frame(parent, bg=CARD)
        info_frame.pack(fill="x", padx=12, pady=5)
        
        tk.Label(info_frame, 
                 text="Your bill is calculated based on how many meals you consumed according to your daily polls.\n"
                      "Standard Rates: Breakfast: Rs. 40, Lunch: Rs. 60, Snacks: Rs. 20, Dinner: Rs. 50\n"
                      "Due Date: 5th of the following month. Fine: Rs. 10/day for late payments.",
                 bg=CARD, fg=MUTED, font=(FONT, 9), justify="left").pack(anchor="w")

        tree = make_tree(parent, columns=("ID", "Month/Year", "Amount (Rs)", "Fine (Rs)", "Due", "Paid On", "Status"),
                         col_widths=[50, 90, 100, 80, 100, 100, 90])
        records = db.get_mess_bills(student_id=self.user["id"])
        
        for row in records:
            month_name = date(row["year"], row["month"], 1).strftime("%b %Y")
            tree.insert("", "end", iid=str(row["id"]), values=(
                row["id"], month_name,
                f"Rs {row['amount']:.2f}",
                f"Rs {row['fine']:.2f}",
                str(row["due_date"]),
                str(row["payment_date"]) if row["payment_date"] else "-",
                row["status"].capitalize(),
            ))
            
        if not records:
            tree.insert("", "end", values=("-","-","No records","-","-","-","-"))

        btn_frame = tk.Frame(parent, bg=CARD)
        btn_frame.pack(fill="x", padx=12, pady=6)
        tk.Button(btn_frame, text="Pay Selected Bill", bg=ACCENT, fg=TEXT, bd=0, padx=14, pady=6,
                  cursor="hand2", command=lambda: self._pay_mess_bill(tree)).pack(side="left", padx=4)
        tk.Label(btn_frame, text="Select a pending row and click Pay.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side="left", padx=10)

    def _pay_mess_bill(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a bill to pay.")
            return
        bill_id = int(sel[0])
        status = tree.item(bill_id)["values"][6]
        
        if status == "Paid":
            messagebox.showinfo("Already Paid", "This bill is already paid.")
            return
        if status == "Processing":
            messagebox.showinfo("Processing", "This bill is already awaiting admin confirmation.")
            return
            
        db.request_pay_mess_bill(bill_id)
        messagebox.showinfo("Success", "Payment initiated. Awaiting admin confirmation.")
        
        # Refresh tree records
        tree.delete(*tree.get_children())
        records = db.get_mess_bills(student_id=self.user["id"])
        for row in records:
            month_name = date(row["year"], row["month"], 1).strftime("%b %Y")
            tree.insert("", "end", iid=str(row["id"]), values=(
                row["id"], month_name,
                f"Rs {row['amount']:.2f}",
                f"Rs {row['fine']:.2f}",
                str(row["due_date"]),
                str(row["payment_date"]) if row["payment_date"] else "-",
                row["status"].capitalize(),
            ))

    # ── Poll (4-meal dish voting) ───────────────────────────────
    def _tab_poll(self, parent):
        tomorrow          = date.today() + timedelta(days=1)
        self._poll_date   = tomorrow
        self._poll_parent = parent
        self._render_poll()

    def _render_poll(self):
        parent = self._poll_parent
        for w in parent.winfo_children():
            w.destroy()

        tomorrow = self._poll_date
        now      = datetime.now()
        closed   = (now.hour == 23 and now.minute >= 59) or now.hour > 23

        # Header
        tk.Label(parent,
                 text=f"Food Poll for Tomorrow — {tomorrow.strftime('%A, %d %b %Y')}",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

        # Deadline banner
        if closed:
            banner = tk.Frame(parent, bg="#7f1d1d")
            banner.pack(fill="x", padx=12, pady=(0, 8))
            tk.Label(banner,
                     text="⛔  Polling is closed for tonight (11:59 PM). Your votes are locked in.",
                     bg="#7f1d1d", fg="#fca5a5", font=(FONT, 10, "bold")).pack(padx=12, pady=6)
        else:
            mins_left = (23 - now.hour) * 60 + (59 - now.minute)
            banner = tk.Frame(parent, bg="#1a3a1a")
            banner.pack(fill="x", padx=12, pady=(0, 8))
            tk.Label(banner,
                     text=f"🕐  Poll closes at 11:59 PM tonight — {mins_left} min remaining. You can change votes anytime before then.",
                     bg="#1a3a1a", fg=HIGHLIGHT, font=(FONT, 9)).pack(padx=12, pady=5)

        # Load menu for tomorrow's weekday and existing poll
        day_name   = tomorrow.strftime("%A")
        week_start = get_week_start()
        # If tomorrow is next week's Monday, adjust week_start
        if tomorrow.weekday() < date.today().weekday():
            week_start = week_start + timedelta(days=7)
        menu_data  = db.get_menu_for_week(week_start)
        existing   = db.get_student_meal_poll(self.user["id"], tomorrow)

        self._poll_vars = {}

        scroll_outer = tk.Frame(parent, bg=CARD)
        scroll_outer.pack(fill="both", expand=True, padx=12, pady=4)

        for meal in MEALS:
            dishes = [r["items"] for r in menu_data
                      if r["day_of_week"] == day_name and r["meal_type"] == meal]
            item_name = dishes[0] if dishes else ""

            section = tk.LabelFrame(scroll_outer, text=f"  {meal}  ",
                                    bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold"),
                                    labelanchor="nw")
            section.pack(fill="x", pady=6)

            var_eat = tk.BooleanVar(value=False)
            var_veg = tk.BooleanVar(value=False)
            self._poll_vars[meal.lower()] = {'eat': var_eat, 'veg': var_veg, 'item': item_name}

            col = meal.lower()
            saved = existing[col] if existing and existing.get(col) else None
            
            # Pre-fill logic
            if saved:
                var_eat.set(True)
                if "(Veg)" in saved:
                    var_veg.set(True)

            cb_state = tk.DISABLED if closed else tk.NORMAL

            if not item_name:
                tk.Label(section, text="No menu set for this meal",
                         bg=CARD, fg=MUTED, font=(FONT, 9, "italic")).pack(anchor="w", padx=12, pady=8)
            else:
                eat_text = f"Eat {meal}: {item_name}"
                main_cb = tk.Checkbutton(section, text=eat_text, variable=var_eat,
                                         bg=CARD, fg=TEXT, selectcolor=SIDEBAR,
                                         activebackground=CARD, activeforeground=TEXT,
                                         font=(FONT, 10), state=cb_state)
                main_cb.pack(anchor="w", padx=12, pady=(8,2))

                is_non_veg = any(kw in item_name.lower() for kw in ["chicken", "mutton", "fish", "egg", "beef", "pork", "meat"])
                if is_non_veg:
                    veg_cb = tk.Checkbutton(section, text="Opt for Veg Alternative", variable=var_veg,
                                            bg=CARD, fg=HIGHLIGHT, selectcolor=SIDEBAR,
                                            activebackground=CARD, activeforeground=HIGHLIGHT,
                                            font=(FONT, 9, "italic"), state=cb_state)
                    veg_cb.pack(anchor="w", padx=32, pady=(0,8))
                else:
                    tk.Frame(section, bg=CARD, height=8).pack()

        # Submit and refresh buttons
        btn_row = tk.Frame(parent, bg=CARD)
        btn_row.pack(fill="x", padx=12, pady=8)
        if not closed:
            tk.Button(btn_row, text="Submit / Update All Polls", bg=ACCENT, fg=TEXT,
                      bd=0, padx=16, pady=8, cursor="hand2",
                      command=self._submit_meal_poll).pack(side="left", padx=4)
        tk.Button(btn_row, text="🔄 Refresh", bg=SIDEBAR, fg=MUTED,
                  bd=0, padx=12, pady=8, cursor="hand2",
                  command=self._render_poll).pack(side="left", padx=4)

        # Live poll totals for tomorrow
        tk.Label(parent, text="Live Poll Standings for Tomorrow:",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 10, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        self._draw_poll_bars(parent, tomorrow)

    def _draw_poll_bars(self, parent, poll_date):
        totals = db.get_meal_poll_totals(poll_date)
        if not totals:
            tk.Label(parent, text="No votes submitted yet.",
                     bg=CARD, fg=MUTED, font=(FONT, 10)).pack(anchor="w", padx=16)
            return
        # Group by meal
        by_meal = {}
        for row in totals:
            meal = row["meal"]
            by_meal.setdefault(meal, []).append(row)

        for meal in MEALS:
            if meal not in by_meal:
                continue
            tk.Label(parent, text=meal, bg=CARD, fg=MUTED,
                     font=(FONT, 9, "bold")).pack(anchor="w", padx=16, pady=(4, 0))
            for row in by_meal[meal]:
                line = tk.Frame(parent, bg=SIDEBAR)
                line.pack(fill="x", padx=20, pady=2)
                tk.Label(line, text=row["dish"][:35], bg=SIDEBAR, fg=TEXT,
                         font=(FONT, 9), width=36, anchor="w").pack(side="left", padx=8)
                bar_w = min(int(row["votes"]) * 18, 280)
                tk.Frame(line, bg=ACCENT2, width=bar_w, height=16).pack(side="left")
                tk.Label(line, text=f"  {row['votes']} votes", bg=SIDEBAR, fg=MUTED,
                         font=(FONT, 8)).pack(side="left")

    def _submit_meal_poll(self):
        vals = {}
        for meal in MEALS:
            data = self._poll_vars[meal.lower()]
            if data['eat'].get() and data['item']:
                if data['veg'].get():
                    vals[meal.lower()] = f"(Veg) {data['item']}"
                else:
                    vals[meal.lower()] = data['item']
            else:
                vals[meal.lower()] = None

        db.submit_meal_poll(
            self.user["id"], self._poll_date,
            vals["breakfast"], vals["lunch"], vals["snacks"], vals["dinner"]
        )
        messagebox.showinfo("Submitted", "Your meal polls have been saved! You can update them anytime before 11:59 PM.")
        self._render_poll()

    # ── Feedback ───────────────────────────────────────────────
    def _tab_feedback(self, parent):
        tk.Label(parent, text="Rate Your Mess Experience",
                 bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(parent, text="Your feedback helps improve the quality of meals served.",
                 bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=12, pady=(0, 10))

        # Star rating
        star_frame = tk.Frame(parent, bg=CARD)
        star_frame.pack(anchor="w", padx=12, pady=4)
        tk.Label(star_frame, text="Rating:", bg=CARD, fg=TEXT, font=(FONT, 10)).pack(side="left", padx=(0, 8))
        self._star_widget = StarRating(star_frame)
        self._star_widget.pack(side="left")
        self._star_label  = tk.Label(star_frame, text="", bg=CARD, fg=MUTED, font=(FONT, 9))
        self._star_label.pack(side="left", padx=8)

        def update_label():
            r = self._star_widget.get()
            label_text = ["", "Poor", "Fair", "Good", "Very Good", "Excellent"][r] if r else ""
            self._star_label.config(text=label_text)
            parent.after(200, update_label)
        update_label()

        # Comment
        tk.Label(parent, text="Comment (optional):", bg=CARD, fg=TEXT,
                 font=(FONT, 10)).pack(anchor="w", padx=12, pady=(8, 2))
        self._fb_comment = scrolledtext.ScrolledText(parent, bg=SIDEBAR, fg=TEXT,
                                                      font=(FONT, 10), wrap="word",
                                                      relief="flat", bd=0, height=4)
        self._fb_comment.pack(fill="x", padx=12, pady=4)

        tk.Button(parent, text="Submit Feedback", bg=ACCENT, fg=TEXT, bd=0, padx=14, pady=7,
                  cursor="hand2", command=self._submit_feedback).pack(anchor="w", padx=12, pady=6)

        # Previous feedback
        tk.Label(parent, text="Your Previous Feedback:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self._fb_tree = make_tree(parent,
                                   columns=("Date", "Rating", "Comment"),
                                   col_widths=[120, 80, 400])
        self._load_fb_tree()

    def _load_fb_tree(self):
        self._fb_tree.delete(*self._fb_tree.get_children())
        past = db.get_feedback_by_student(self.user["id"])
        for row in past:
            stars = "★" * row["rating"] + "☆" * (5 - row["rating"])
            self._fb_tree.insert("", "end", values=(
                str(row["created_at"])[:10], stars,
                (row["comment"] or "")[:80],
            ))
        if not past:
            self._fb_tree.insert("", "end", values=("-", "No feedback yet", ""))

    def _submit_feedback(self):
        rating = self._star_widget.get()
        if not rating:
            messagebox.showinfo("Rating Required", "Please select a star rating (1–5).")
            return
        comment = self._fb_comment.get("1.0", "end").strip()
        db.add_feedback(self.user["id"], rating, comment)
        messagebox.showinfo("Thank You!", "Your feedback has been submitted successfully.")
        self._star_widget.reset()
        self._fb_comment.delete("1.0", "end")
        self._load_fb_tree()



    # ── Notifications ──────────────────────────────────────────
    def _tab_notifications(self, parent):
        tk.Label(parent, text="Notifications from Admin", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        notifications = db.get_notifications("student")
        container = make_scrollable_container(parent)
        if not notifications:
            tk.Label(container, text="No notifications yet.",
                     bg=CARD, fg=MUTED, font=(FONT, 10)).pack(pady=20)
            return
        for n in notifications:
            card = tk.Frame(container, bg=SIDEBAR, bd=0, relief="flat")
            card.pack(fill="x", padx=8, pady=4)
            hdr = tk.Frame(card, bg=ACCENT)
            hdr.pack(fill="x")
            tk.Label(hdr, text=f"  {n['title']}", bg=ACCENT, fg=TEXT,
                     font=(FONT, 10, "bold")).pack(side="left", padx=8, pady=4)
            tk.Label(hdr, text=str(n["created_at"])[:16], bg=ACCENT, fg="#d8f3dc",
                     font=(FONT, 8)).pack(side="right", padx=8)
            tk.Label(card, text=n["message"], bg=SIDEBAR, fg=TEXT,
                     font=(FONT, 10), wraplength=700, justify="left").pack(anchor="w", padx=12, pady=8)

    # ── Complaints ─────────────────────────────────────────────
    def _tab_complaints(self, parent):
        tk.Label(parent, text="Submit Complaint / Suggestion", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        text_area = scrolledtext.ScrolledText(parent, bg=SIDEBAR, fg=TEXT,
                                              font=(FONT, 10), wrap="word",
                                              relief="flat", bd=0, height=6)
        text_area.pack(fill="x", padx=12, pady=6)
        text_area.insert("1.0", "Type your complaint or suggestion here...")
        text_area.bind("<FocusIn>",
                       lambda _e: text_area.delete("1.0", "end")
                       if text_area.get("1.0", "end").strip().startswith("Type") else None)

        tk.Button(parent, text="Submit", bg=ACCENT, fg=TEXT, bd=0, padx=16, pady=6,
                  cursor="hand2",
                  command=lambda: self._submit_complaint(text_area)).pack(anchor="w", padx=12)

        tk.Label(parent, text="Your Previous Complaints:", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", padx=12, pady=(14, 2))
        tree = make_tree(parent, columns=("Date","Message","Status"),
                         col_widths=[120, 400, 100])
        for c in db.get_complaints(user_id=self.user["id"]):
            tree.insert("", "end", values=(
                str(c["created_at"])[:10],
                c["message"][:80] + ("..." if len(c["message"]) > 80 else ""),
                c["status"].capitalize(),
            ))

    def _submit_complaint(self, text_area):
        msg = text_area.get("1.0", "end").strip()
        if not msg or msg.startswith("Type"):
            messagebox.showinfo("Empty", "Please type a complaint or suggestion.")
            return
        db.add_complaint(self.user["id"], msg)
        messagebox.showinfo("Submitted", "Your complaint has been submitted.")
        text_area.delete("1.0", "end")

    # ── Manual ─────────────────────────────────────────────────
    def _tab_manual(self, parent):
        tk.Label(parent, text="User Manual", bg=CARD, fg=HIGHLIGHT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        text = scrolledtext.ScrolledText(parent, bg=SIDEBAR, fg=TEXT, font=(FONT, 10),
                                         wrap="word", relief="flat", bd=0)
        text.pack(fill="both", expand=True, padx=12, pady=8)
        text.insert("1.0", db.get_manual("student"))
        text.config(state="disabled")

    # ── Midnight reset ─────────────────────────────────────────
    def _schedule_midnight_reset(self):
        now      = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=5)
        ms_until = int((midnight - now).total_seconds() * 1000)
        self.after(ms_until, self._midnight_reset)

    def _midnight_reset(self):
        self._poll_date = date.today() + timedelta(days=1)
        self._render_poll()
        self._schedule_midnight_reset()
