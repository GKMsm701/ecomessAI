"""
login_page.py — EcoMess Login Page (Modern Redesign v4)
─────────────────────────────────────────────────────────
• Floating card with multi-layer canvas glow effect
• Animated particle / shimmer background
• Pill-style role selector with slide animation
• Glowing input fields with icon prefixes
• Gradient Sign-In button with shimmer sweep on hover
• Shake + red-flash on bad login
• Braille spinner while authenticating
• Green pulse + success tick on good login
• ← Back to Home no longer breaks navigation (calls app.show_login() safely)

All original functions preserved:
  _login(), _forgot_password(), app.on_login_success(user)
"""

import tkinter as tk
from tkinter import messagebox
import math, random, time
import database as db

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = "#080f0b"
CARD_BG     = "#0e1c13"
CARD_BORDER = "#1a3d26"
GLOW        = "#3ddc84"
GLOW_DIM    = "#1a5c38"
GLOW_DARK   = "#0d2e1c"
FIELD_BG    = "#0b1710"
FIELD_BD    = "#1f4a2e"
ACCENT      = "#3ddc84"
ACCENT2     = "#2ab869"
ACCENT3     = "#1a7a48"
TEXT        = "#d4ede0"
TEXT2       = "#7fb896"
TEXT3       = "#3d6e52"
RED         = "#ff4f4f"
RED_DIM     = "#3d0d0d"
AMBER       = "#f5a623"
CYAN        = "#00f5d4"
FONT        = "Segoe UI"
FONT_B      = "Segoe UI Semibold"
FONT_MONO   = "Consolas"

# ── Particle config ────────────────────────────────────────────────────────────
N_PARTICLES = 28


# ══════════════════════════════════════════════════════════════════════════════
class LoginPage(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app         = app
        self._spinner_id = None
        self._spinner_i  = 0
        self._shake_id   = None
        self._anim_id    = None
        self._particles  = []
        self._shimmer_x  = -1.0      # shimmer sweep position (0..1)
        self._shimmer_dir = 1
        self._build()
        self._start_particles()

    # ─────────────────────────────────────── Teardown ───────────────────────
    def destroy(self):
        """Cancel all after() jobs before destroying."""
        for attr in ("_spinner_id", "_shake_id", "_anim_id"):
            jid = getattr(self, attr, None)
            if jid:
                try: self.after_cancel(jid)
                except Exception: pass
        super().destroy()

    # ─────────────────────────────────────── Background canvas ──────────────
    def _build(self):
        # Full-window canvas for animated background
        self._bg = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._bg.bind("<Configure>", self._on_resize)

        # Center host frame (sits on top of canvas)
        host = tk.Frame(self, bg=BG)
        host.place(relx=0.5, rely=0.5, anchor="center")
        self._build_card(host)

    def _on_resize(self, e=None):
        self._init_particles()

    # ─────────────────────────────────────── Particles ──────────────────────
    def _init_particles(self):
        self._bg.delete("particle")
        w = self._bg.winfo_width()
        h = self._bg.winfo_height()
        if w < 2 or h < 2:
            return
        self._particles = []
        for _ in range(N_PARTICLES):
            x  = random.uniform(0, w)
            y  = random.uniform(0, h)
            r  = random.uniform(1, 3)
            dx = random.uniform(-0.3, 0.3)
            dy = random.uniform(-0.5, -0.1)
            op = random.uniform(0.2, 0.8)      # "opacity" stored as float
            self._particles.append([x, y, r, dx, dy, op])

    def _start_particles(self):
        self._animate()

    def _animate(self):
        c = self._bg
        w = c.winfo_width()
        h = c.winfo_height()
        c.delete("particle")

        for p in self._particles:
            x, y, r, dx, dy, op = p
            # colour based on opacity
            val  = int(op * 180)
            col  = f"#{val:02x}{min(255,val+80):02x}{val:02x}"
            c.create_oval(x - r, y - r, x + r, y + r,
                          fill=col, outline="", tags="particle")
            # move
            p[0] = (x + dx) % (w + 4)
            p[1] = y + dy
            if p[1] < -4:
                p[1] = h + 4
                p[0] = random.uniform(0, w)

        self._anim_id = self.after(40, self._animate)

    # ─────────────────────────────────────── Card ───────────────────────────
    def _build_card(self, parent):
        # Outer glow ring
        glow_ring = tk.Canvas(parent, width=420, height=2,
                              bg=BG, highlightthickness=0)
        glow_ring.pack()
        glow_ring.create_line(0, 1, 420, 1, fill=GLOW_DIM, width=1)

        # Card frame
        self._card = tk.Frame(parent, bg=CARD_BG,
                              highlightbackground=CARD_BORDER,
                              highlightthickness=1)
        self._card.pack(padx=0, pady=0)

        pad = tk.Frame(self._card, bg=CARD_BG, padx=50, pady=40)
        pad.pack()
        self._pad = pad

        self._build_logo(pad)
        self._build_role_tabs(pad)
        self._build_inst_type(pad)   # unified establishment personalizer
        self._build_username(pad)
        self._build_password(pad)
        self._build_extras(pad)
        self._build_status(pad)
        self._build_signin_btn(pad)
        self._build_demo_accounts(pad)
        self._build_footer(pad)

    # ─────────────────────────────────────── Logo ───────────────────────────
    def _build_logo(self, p):
        # Glowing circle badge
        badge = tk.Canvas(p, width=70, height=70, bg=CARD_BG,
                          highlightthickness=0)
        badge.pack(pady=(0, 6))
        # Glow rings
        for r, col, w in [(34, "#0d2e1c", 8), (30, "#1a5c38", 4),
                          (26, "#2ab869", 2)]:
            badge.create_oval(35 - r, 35 - r, 35 + r, 35 + r,
                              outline=col, width=w, fill="")
        badge.create_oval(12, 12, 58, 58, fill=GLOW_DARK, outline=ACCENT, width=2)
        badge.create_text(35, 35, text="🌿", font=(FONT, 22))

        tk.Label(p, text="EcoMess", bg=CARD_BG, fg=ACCENT,
                 font=("Segoe UI", 30, "bold")).pack(pady=(4, 1))

        tk.Label(p, text="INSTITUTION & PRIVATE KITCHEN FOOD MGMT",
                 bg=CARD_BG, fg=TEXT3,
                 font=(FONT_MONO, 7, "bold")).pack()

        # Gradient-ish separator (canvas line with fade)
        sep = tk.Canvas(p, width=320, height=6, bg=CARD_BG,
                        highlightthickness=0)
        sep.pack(pady=(16, 0))
        for i in range(320):
            t   = abs(i / 160 - 1)          # 0 at center, 1 at edges
            val = int((1 - t) * 80)
            col = f"#00{val:02x}00" if val else CARD_BG
            sep.create_line(i, 3, i, 4, fill=col)

        tk.Label(p, text="Unified Food Waste & Surplus Redistribution Platform",
                 bg=CARD_BG, fg=TEXT2,
                 font=(FONT, 9)).pack(pady=(14, 20))

    # ─────────────────────────────────────── Role tabs ──────────────────────
    def _build_role_tabs(self, p):
        tk.Label(p, text="ROLE", bg=CARD_BG, fg=TEXT3,
                 font=(FONT_MONO, 7, "bold")).pack(anchor="w")

        self.role_var = tk.StringVar(value="student")

        outer = tk.Frame(p, bg=FIELD_BD, padx=1, pady=1)
        outer.pack(fill="x", pady=(6, 16))

        row = tk.Frame(outer, bg=FIELD_BG)
        row.pack(fill="x")

        self._role_btns = {}
        roles_list = [
            ("🎓", "Student", "student"),
            ("🍽", "Staff",   "staff"),
            ("⚙", "Admin",   "admin"),
            ("🏢", "Middleman", "middleman"),
            ("🤝", "NGO",     "ngo")
        ]
        for icon, label, val in roles_list:
            btn = tk.Button(row, text=f"{icon} {label}",
                            font=(FONT_B, 8, "bold"),
                            bd=0, relief="flat", cursor="hand2",
                            padx=3, pady=8,
                            command=lambda v=val: self._select_role(v))
            btn.pack(side="left", expand=True, fill="x")
            self._role_btns[val] = btn
            btn.bind("<Enter>", lambda e, b=btn, v=val: self._role_hover(b, v, True))
            btn.bind("<Leave>", lambda e, b=btn, v=val: self._role_hover(b, v, False))

        self._select_role("student")

    # ──────────────────────────────── Unified Establishment Section ──────────
    def _build_inst_type(self, p):
        """Unified establishment personalizer: Institution vs Private Kitchen."""
        from tkinter import ttk
        self._inst_frame = tk.Frame(p, bg=CARD_BG)

        # Title
        hdr = tk.Frame(self._inst_frame, bg=CARD_BG)
        hdr.pack(fill="x", pady=(0, 2))
        tk.Label(hdr, text="ESTABLISHMENT CATEGORY",
                 bg=CARD_BG, fg=TEXT3,
                 font=("Consolas", 7, "bold")).pack(side="left")

        # Two category buttons: Institution vs Private Kitchen
        cat_bar = tk.Frame(self._inst_frame, bg=FIELD_BD, padx=1, pady=1)
        cat_bar.pack(fill="x", pady=(2, 6))
        cat_inner = tk.Frame(cat_bar, bg=FIELD_BG)
        cat_inner.pack(fill="x")

        self.est_category_var = tk.StringVar(value="institution")
        self._cat_btns = {}

        for cat_key, cat_label in [
            ("institution", "🏛 Institution"),
            ("private_kitchen", "🍳 Private Kitchen")
        ]:
            b = tk.Button(cat_inner, text=cat_label,
                          font=(FONT_B, 8, "bold"), bd=0, relief="flat", cursor="hand2",
                          padx=4, pady=5,
                          command=lambda k=cat_key: self._select_category(k))
            b.pack(side="left", expand=True, fill="x")
            self._cat_btns[cat_key] = b

        # Subtype row
        outer = tk.Frame(self._inst_frame, bg=FIELD_BD, padx=1, pady=1)
        outer.pack(fill="x", pady=(0, 4))
        inner = tk.Frame(outer, bg=FIELD_BG)
        inner.pack(fill="x")

        self._est_icon_lbl = tk.Label(inner, text="🏛", bg=FIELD_BG, fg=TEXT3, font=(FONT, 11))
        self._est_icon_lbl.pack(side="left", padx=(8, 4))
        tk.Frame(inner, bg=FIELD_BD, width=1).pack(side="left", fill="y", pady=4)

        self.inst_type_var = tk.StringVar(value="hostel")
        self._inst_cb = ttk.Combobox(inner, textvariable=self.inst_type_var,
                                     state="readonly", width=22,
                                     font=(FONT, 9))
        self._inst_cb.pack(side="left", padx=8, pady=5, fill="x", expand=True)

        # Subtitle descriptor
        self._est_sub_lbl = tk.Label(self._inst_frame, text="", bg=CARD_BG, fg=TEXT3,
                                     font=(FONT, 7), wraplength=320, justify="left")
        self._est_sub_lbl.pack(anchor="w", pady=(0, 10))

        # Middleman / NGO Info banner
        self._info_banner = tk.Frame(p, bg="#112233", padx=10, pady=8, relief="ridge", bd=1)
        self._info_banner_lbl = tk.Label(self._info_banner, text="", bg="#112233", fg=CYAN,
                                         font=(FONT, 8), wraplength=300, justify="left")
        self._info_banner_lbl.pack(fill="x")
        self._info_banner.pack_forget()

        self._select_category("institution")

    def _select_category(self, cat):
        self.est_category_var.set(cat)
        for k, btn in self._cat_btns.items():
            if k == cat:
                btn.config(bg=ACCENT, fg="#050f08")
            else:
                btn.config(bg=FIELD_BG, fg=TEXT2)

        if cat == "institution":
            self._est_icon_lbl.config(text="🏛")
            opts = [
                "hostel", "school", "college", "midday_meal",
                "hospital", "staff_hostel"
            ]
            self._inst_cb.config(values=opts)
            if self.inst_type_var.get() not in opts:
                self.inst_type_var.set("hostel")
            self._est_sub_lbl.config(
                text="Hostels, Schools, Colleges, Midday Meal Scheme, Hospitals"
            )
        else:
            self._est_icon_lbl.config(text="🍳")
            opts = [
                "canteen", "working_womens_hostel", "restaurant",
                "catering", "cloud_kitchen", "cafeteria"
            ]
            self._inst_cb.config(values=opts)
            if self.inst_type_var.get() not in opts:
                self.inst_type_var.set("canteen")
            self._est_sub_lbl.config(
                text="Canteens, Working Women's Hostels, Restaurants, Catering Units"
            )

    def _select_role(self, role):
        self.role_var.set(role)
        for val, btn in self._role_btns.items():
            if val == role:
                btn.config(bg=ACCENT, fg="#050f08",
                           activebackground=ACCENT2,
                           activeforeground="#050f08")
            else:
                btn.config(bg=FIELD_BG, fg=TEXT2,
                           activebackground=GLOW_DARK,
                           activeforeground=ACCENT)

        # Show/hide establishment selector and info banners
        if hasattr(self, '_inst_frame') and hasattr(self, '_info_banner'):
            if role in ("admin", "staff", "student"):
                self._info_banner.pack_forget()
                self._inst_frame.pack(fill="x", before=getattr(self, '_u_border', None))
            elif role == "middleman":
                self._inst_frame.pack_forget()
                self._info_banner_lbl.config(
                    text="🌐 Middleman Platform Organization:\nCoordinates food preparation planning, surplus redistribution, multi-source pooling, route optimization, disaster relief & closed-loop biogas recovery."
                )
                self._info_banner.pack(fill="x", before=getattr(self, '_u_border', None), pady=(0, 10))
            elif role in ("ngo", "buyer"):
                self._inst_frame.pack_forget()
                self._info_banner_lbl.config(
                    text="🤝 Relief Organization & NGO:\nAccesses redistributed surplus meals, places bulk reservations, and requests multi-source allocations."
                )
                self._info_banner.pack(fill="x", before=getattr(self, '_u_border', None), pady=(0, 10))
            else:
                self._inst_frame.pack_forget()
                self._info_banner.pack_forget()

    def _role_hover(self, btn, val, on):
        if val == self.role_var.get():
            btn.config(bg=ACCENT2 if on else ACCENT)
        else:
            btn.config(bg="#122018" if on else FIELD_BG,
                       fg=ACCENT   if on else TEXT2)

    # ─────────────────────────────────────── Field helper ───────────────────
    def _make_field(self, parent, icon, var, show=None):
        """Returns (border_frame, entry_widget)."""
        border = tk.Frame(parent, bg=FIELD_BD, padx=1, pady=1)
        border.pack(fill="x", pady=(5, 0))

        inner = tk.Frame(border, bg=FIELD_BG)
        inner.pack(fill="x")

        # Icon label
        tk.Label(inner, text=icon, bg=FIELD_BG, fg=TEXT3,
                 font=(FONT, 12)).pack(side="left", padx=(10, 4))

        # Separator
        tk.Frame(inner, bg=FIELD_BD, width=1).pack(side="left",
                                                    fill="y", pady=6)

        kw = {"show": show} if show else {}
        ent = tk.Entry(inner, textvariable=var,
                       bg=FIELD_BG, fg=TEXT,
                       insertbackground=ACCENT,
                       font=(FONT, 11), relief="flat", bd=0,
                       width=22, **kw)
        ent.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        ent.bind("<FocusIn>",
            lambda e, b=border: (b.config(bg=ACCENT),
                                 inner.config(bg=FIELD_BG)))
        ent.bind("<FocusOut>",
            lambda e, b=border: b.config(bg=FIELD_BD))
        return border, ent

    # ─────────────────────────────────────── Username ───────────────────────
    def _build_username(self, p):
        tk.Label(p, text="USERNAME", bg=CARD_BG, fg=TEXT3,
                 font=(FONT_MONO, 7, "bold")).pack(anchor="w")
        self.username_var    = tk.StringVar()
        self._u_border, self._uentry = self._make_field(
            p, "👤", self.username_var)
        self._uentry.focus_set()
        tk.Frame(p, height=14, bg=CARD_BG).pack()       # spacer

    # ─────────────────────────────────────── Password ───────────────────────
    def _build_password(self, p):
        tk.Label(p, text="PASSWORD", bg=CARD_BG, fg=TEXT3,
                 font=(FONT_MONO, 7, "bold")).pack(anchor="w")

        self._show_pwd  = tk.BooleanVar(value=False)
        self.pwd_var    = tk.StringVar()
        self._p_border, self._pentry = self._make_field(
            p, "🔑", self.pwd_var, show="●")
        self._pentry.bind("<Return>", lambda e: self._login())

        # Eye button sits inside the border's inner frame
        inner = self._p_border.winfo_children()[0]   # the inner Frame
        self._eye_btn = tk.Button(
            inner, text="🔒",
            bg=FIELD_BG, fg=TEXT3,
            font=(FONT, 12),
            relief="flat", bd=0, cursor="hand2",
            padx=6, pady=0,
            activebackground=GLOW_DARK,
            activeforeground=ACCENT,
            command=self._toggle_password)
        self._eye_btn.pack(side="right", padx=(0, 6))
        self._eye_btn.bind("<Enter>",
            lambda e: self._eye_btn.config(fg=ACCENT, bg=GLOW_DARK))
        self._eye_btn.bind("<Leave>",
            lambda e: self._eye_btn.config(
                fg=ACCENT if self._show_pwd.get() else TEXT3,
                bg=FIELD_BG))

    def _toggle_password(self):
        self._show_pwd.set(not self._show_pwd.get())
        if self._show_pwd.get():
            self._pentry.config(show="")
            self._eye_btn.config(text="👁", fg=ACCENT)
        else:
            self._pentry.config(show="●")
            self._eye_btn.config(text="🔒", fg=TEXT3)

    # ─────────────────────────────────────── Extras row ─────────────────────
    def _build_extras(self, p):
        row = tk.Frame(p, bg=CARD_BG)
        row.pack(fill="x", pady=(8, 0))

        show = tk.Label(row, text="👁  Show password",
                        bg=CARD_BG, fg=TEXT3,
                        font=(FONT, 8), cursor="hand2")
        show.pack(side="left")
        show.bind("<Button-1>", lambda e: self._toggle_password())
        show.bind("<Enter>", lambda e: show.config(fg=ACCENT))
        show.bind("<Leave>", lambda e: show.config(fg=TEXT3))

        fp = tk.Label(row, text="Forgot password? →",
                      bg=CARD_BG, fg=ACCENT3,
                      font=(FONT, 8), cursor="hand2")
        fp.pack(side="right")
        fp.bind("<Button-1>", lambda e: self._forgot_password())
        fp.bind("<Enter>",
            lambda e: fp.config(fg=ACCENT, font=(FONT, 8, "underline")))
        fp.bind("<Leave>",
            lambda e: fp.config(fg=ACCENT3, font=(FONT, 8)))

    # ─────────────────────────────────────── Status ──────────────────────────
    def _build_status(self, p):
        self.status_var  = tk.StringVar()
        self._status_lbl = tk.Label(p, textvariable=self.status_var,
                                    bg=CARD_BG, fg=RED,
                                    font=(FONT, 9), wraplength=320)
        self._status_lbl.pack(pady=(14, 4))

    # ─────────────────────────────────────── Sign In btn ────────────────────
    def _build_signin_btn(self, p):
        # Canvas-drawn gradient button
        self._btn_canvas = tk.Canvas(p, width=320, height=48,
                                     bg=CARD_BG, highlightthickness=0,
                                     cursor="hand2")
        self._btn_canvas.pack(pady=(4, 0))
        self._draw_btn(hover=False)
        self._btn_canvas.bind("<Enter>",    lambda e: self._draw_btn(True))
        self._btn_canvas.bind("<Leave>",    lambda e: self._draw_btn(False))
        self._btn_canvas.bind("<Button-1>", lambda e: self._login())

    def _draw_btn(self, hover=False, text="Sign In  →", disabled=False):
        c = self._btn_canvas
        c.delete("all")
        w, h = 320, 48
        # Gradient fill (left dark → right bright)
        for i in range(w):
            t   = i / w
            if disabled:
                r = int(0x1e * (1 - t) + 0x1a * t)
                g = int(0x6e * (1 - t) + 0x5c * t)
                b = int(0x43 * (1 - t) + 0x38 * t)
            elif hover:
                r = int(0x2a * (1 - t) + 0x3d * t)
                g = int(0xb8 * (1 - t) + 0xdc * t)
                b = int(0x69 * (1 - t) + 0x84 * t)
            else:
                r = int(0x3d * (1 - t) + 0x2a * t)
                g = int(0xdc * (1 - t) + 0xb8 * t)
                b = int(0x84 * (1 - t) + 0x69 * t)
            col = f"#{r:02x}{g:02x}{b:02x}"
            c.create_line(i, 0, i, h, fill=col)

        # Shimmer stripe on hover
        if hover and not disabled:
            sx = int(self._shimmer_x * w)
            for i in range(max(0, sx - 30), min(w, sx + 30)):
                t2  = 1 - abs(i - sx) / 30
                val = int(t2 * 60)
                c.create_line(i, 0, i, h,
                              fill=f"#{min(255,0x3d+val):02x}"
                                   f"{min(255,0xdc+val):02x}"
                                   f"{min(255,0x84+val):02x}")

        # Border glow
        c.create_rectangle(0, 0, w - 1, h - 1,
                           outline=ACCENT if not disabled else GLOW_DIM,
                           width=1)

        # Text
        fg = "#050f08" if not disabled else TEXT3
        c.create_text(w // 2, h // 2, text=text,
                      fill=fg, font=(FONT, 12, "bold"))

        # Animate shimmer
        if hover and not disabled:
            self._shimmer_x = (self._shimmer_x + 0.02) % 1.2

    # ─────────────────────────────────────── Demo Accounts ────────────────────
    def _build_demo_accounts(self, p):
        tk.Label(p, text="QUICK DEMO LOGINS", bg=CARD_BG, fg=TEXT3,
                 font=(FONT_MONO, 7, "bold")).pack(anchor="w", pady=(12, 4))

        row1 = tk.Frame(p, bg=CARD_BG)
        row1.pack(fill="x", pady=2)

        row2 = tk.Frame(p, bg=CARD_BG)
        row2.pack(fill="x", pady=2)

        demos_1 = [
            ("🏛 Institution", "admin", "admin123", "admin", "institution", "hostel"),
            ("🍳 Private Kitchen", "chef_suresh", "suresh123", "admin", "private_kitchen", "canteen"),
            ("🏢 Middleman", "middleman", "admin123", "middleman", "middleman", "general"),
        ]
        demos_2 = [
            ("🍽 Staff", "rajan", "rajan123", "staff", "institution", "hostel"),
            ("🎓 Student", "alice", "alice123", "student", "institution", "hostel"),
            ("🤝 Relief NGO", "annapurna", "ngo123", "ngo", "ngo", "general"),
        ]

        for label, u, pwd, r, cat, inst in demos_1:
            btn = tk.Button(row1, text=label, bg=FIELD_BG, fg=TEXT2,
                            font=(FONT, 7), bd=1, relief="solid", padx=2, pady=3, cursor="hand2",
                            command=lambda _u=u, _p=pwd, _r=r, _c=cat, _i=inst: self._quick_fill(_u, _p, _r, _c, _i))
            btn.pack(side="left", expand=True, fill="x", padx=2)

        for label, u, pwd, r, cat, inst in demos_2:
            btn = tk.Button(row2, text=label, bg=FIELD_BG, fg=TEXT2,
                            font=(FONT, 7), bd=1, relief="solid", padx=2, pady=3, cursor="hand2",
                            command=lambda _u=u, _p=pwd, _r=r, _c=cat, _i=inst: self._quick_fill(_u, _p, _r, _c, _i))
            btn.pack(side="left", expand=True, fill="x", padx=2)

    def _quick_fill(self, u, p, r, cat, inst):
        self.username_var.set(u)
        self.pwd_var.set(p)
        self._select_role(r)
        if hasattr(self, '_select_category') and cat in ("institution", "private_kitchen"):
            self._select_category(cat)
            if hasattr(self, 'inst_type_var'):
                self.inst_type_var.set(inst)

    # ─────────────────────────────────────── Footer ──────────────────────────
    def _build_footer(self, p):
        sep = tk.Canvas(p, width=320, height=6, bg=CARD_BG,
                        highlightthickness=0)
        sep.pack(pady=(18, 0))
        for i in range(320):
            t   = abs(i / 160 - 1)
            val = int((1 - t) * 60)
            col = f"#00{val:02x}00" if val else CARD_BG
            sep.create_line(i, 3, i, 4, fill=col)

        back = tk.Label(p, text="← Back to Home",
                        bg=CARD_BG, fg=TEXT3,
                        font=(FONT, 9), cursor="hand2")
        back.pack(pady=(10, 0))
        back.bind("<Button-1>", self._go_home)
        back.bind("<Enter>",
            lambda e: back.config(fg=ACCENT, font=(FONT, 9, "underline")))
        back.bind("<Leave>",
            lambda e: back.config(fg=TEXT3, font=(FONT, 9)))

    def _go_home(self, e=None):
        """
        Navigate back to the home screen safely.
        Tries common method names used in EcoMess main.py.
        """
        for method in ("_show_home", "show_home", "_show_landing",
                       "show_landing", "_show_start"):
            fn = getattr(self.app, method, None)
            if callable(fn):
                fn()
                return
        # Fallback: destroy self and let app handle it
        try:
            self.app.show_login = self._rebuild_login
            self.destroy()
        except Exception:
            pass

    def _rebuild_login(self):
        """Called by app when user wants to return to login."""
        # This reinstates the login page if app calls show_login() again
        for widget in self.app.content.winfo_children():
            widget.destroy()
        LoginPage(self.app.content, self.app).pack(fill="both", expand=True)

    # ══════════════════════════════════════════ Animations ═══════════════════

    def _flash_border(self, border, steps=6):
        colors = [RED, FIELD_BD] * (steps // 2)
        def _do(i=0):
            if i >= len(colors): border.config(bg=FIELD_BD); return
            border.config(bg=colors[i])
            self.after(100, lambda: _do(i + 1))
        _do()

    def _shake(self, step=0):
        if self._shake_id:
            self.after_cancel(self._shake_id)
        deltas = [14, -14, 11, -11, 8, -8, 5, -5, 2, -2, 0]
        if step >= len(deltas):
            self._pad.config(padx=50)
            return
        d = deltas[step]
        left  = max(4, 50 + d)
        right = max(4, 50 - d)
        self._pad.pack_configure(padx=(left, right))
        self._shake_id = self.after(38, lambda: self._shake(step + 1))

    def _pulse_btn(self, steps=6):
        cols = [ACCENT2, ACCENT] * (steps // 2)
        def _do(i=0):
            if i >= len(cols): self._draw_btn(False); return
            c = self._btn_canvas
            c.delete("all")
            c.create_rectangle(0, 0, 319, 47, fill=cols[i], outline=ACCENT)
            c.create_text(160, 24, text="✓  Logging in…",
                          fill="#050f08", font=(FONT, 12, "bold"))
            self.after(90, lambda: _do(i + 1))
        _do()

    _SP = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def _start_spinner(self):
        self._spinner_i = 0
        self._tick_spinner()

    def _tick_spinner(self):
        s = self._SP[self._spinner_i % len(self._SP)]
        self._draw_btn(disabled=True, text=f"{s}  Signing in…")
        self._spinner_i += 1
        self._spinner_id = self.after(80, self._tick_spinner)

    def _stop_spinner(self):
        if self._spinner_id:
            self.after_cancel(self._spinner_id)
            self._spinner_id = None
        self._draw_btn(hover=False)

    # ══════════════════════════════════════════ Core logic ═══════════════════

    def _login(self):
        username = self.username_var.get().strip()
        password = self.pwd_var.get().strip()
        role     = self.role_var.get()
        self.status_var.set("")

        if not username or not password:
            self.status_var.set("⚠  Please enter username and password.")
            self._status_lbl.config(fg=AMBER)
            self._flash_border(self._u_border if not username else self._p_border)
            self._shake()
            return

        self._start_spinner()
        self.update_idletasks()

        try:
            user = db.authenticate(username, password, role)
        except ConnectionError as e:
            self._stop_spinner()
            self.status_var.set(f"🔌  DB Error: {e}")
            self._status_lbl.config(fg=RED)
            return

        self._stop_spinner()

        if user:
            # Save institution_type for admin/staff/student roles
            role = self.role_var.get()
            if role in ("admin", "staff", "student") and hasattr(self, 'inst_type_var'):
                inst_type = self.inst_type_var.get().strip().lower()
                try:
                    db.update_user_institution_type(user["id"], inst_type)
                    user["institution_type"] = inst_type
                except Exception:
                    pass  # Non-critical — dashboard will use default

            self.status_var.set("\u2713  Login successful!")
            self._status_lbl.config(fg=ACCENT)
            self._pulse_btn()
            self.after(560, lambda: self.app.on_login_success(user))
        else:
            self.status_var.set("✘  Invalid credentials or role.")
            self._status_lbl.config(fg=RED)
            self._flash_border(self._u_border)
            self._flash_border(self._p_border)
            self._shake()

    def _forgot_password(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showinfo(
                "Forgot Password",
                "Please enter your username first, then click 'Forgot password?'."
            )
            return
        try:
            conn = db.get_connection()
            cur  = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, full_name FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
            cur.close(); conn.close()
            if user:
                db.forgot_password_request(user["id"])
                messagebox.showinfo(
                    "Request Sent",
                    "Your password reset request has been sent to the Admin.\n"
                    "Please contact the administrator to reset your password."
                )
            else:
                messagebox.showerror(
                    "Not Found", f"No account found with username '{username}'.")
        except Exception as e:
            messagebox.showerror("Error", str(e))