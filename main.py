"""
main.py — EcoMess Main Application Entry Point
Tkinter single-window app with sidebar navigation and frame switching.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import database as db

# ── Theme Colors ──────────────────────────────────────────────
BG        = "#1b2228"       # App background
SIDEBAR   = "#0d1b2a"       # Sidebar background
CARD      = "#1f3040"       # Card / widget bg
ACCENT    = "#2d6a4f"       # Primary green
ACCENT2   = "#40916c"       # Lighter green
HIGHLIGHT = "#74c69d"       # Hover / highlight
TEXT      = "#edf2f4"       # Primary text
MUTED     = "#94a3b8"       # Secondary text
RED       = "#e63946"       # Danger / logout
FONT      = "Segoe UI"


def apply_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, font=(FONT, 10))
    style.configure("TFrame",       background=BG)
    style.configure("Card.TFrame",  background=CARD)
    style.configure("Sidebar.TFrame", background=SIDEBAR)

    style.configure("TLabel",   background=BG,    foreground=TEXT, font=(FONT, 10))
    style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=(FONT, 10))
    style.configure("Title.TLabel", background=BG, foreground=HIGHLIGHT,
                    font=(FONT, 18, "bold"))
    style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=(FONT, 10))
    style.configure("Sidebar.TLabel", background=SIDEBAR, foreground=TEXT, font=(FONT, 11))

    style.configure("TButton",
        background=ACCENT, foreground=TEXT, font=(FONT, 10, "bold"),
        borderwidth=0, padding=(12, 6))
    style.map("TButton",
        background=[("active", ACCENT2)],
        foreground=[("active", TEXT)])

    style.configure("Red.TButton",
        background=RED, foreground=TEXT, font=(FONT, 10, "bold"),
        borderwidth=0, padding=(12, 6))
    style.map("Red.TButton", background=[("active", "#c1121f")])

    style.configure("Nav.TButton",
        background=SIDEBAR, foreground=TEXT, font=(FONT, 10),
        borderwidth=0, padding=(10, 8), anchor="w")
    style.map("Nav.TButton",
        background=[("active", CARD)],
        foreground=[("active", HIGHLIGHT)])

    style.configure("TEntry",
        fieldbackground=CARD, foreground=TEXT, insertcolor=TEXT,
        borderwidth=1, padding=6)

    style.configure("TNotebook",         background=CARD, borderwidth=0)
    style.configure("TNotebook.Tab",
        background=SIDEBAR, foreground=MUTED, font=(FONT, 10),
        padding=(14, 6))
    style.map("TNotebook.Tab",
        background=[("selected", CARD)],
        foreground=[("selected", HIGHLIGHT)])

    style.configure("Treeview",
        background=CARD, foreground=TEXT, fieldbackground=CARD,
        rowheight=28, font=(FONT, 9))
    style.configure("Treeview.Heading",
        background=ACCENT, foreground=TEXT, font=(FONT, 9, "bold"))
    style.map("Treeview", background=[("selected", ACCENT2)])

    style.configure("TCombobox",
        fieldbackground=CARD, background=CARD, foreground=TEXT,
        selectbackground=ACCENT, selectforeground=TEXT)
    style.map("TCombobox", fieldbackground=[("readonly", CARD)])

    style.configure("TScrollbar",
        background=CARD, troughcolor=BG, arrowcolor=MUTED, borderwidth=0)


# ──────────────────────────────────────────────────────────────
#  Main Application
# ──────────────────────────────────────────────────────────────
class EcoMessApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EcoMess — Mess Management System")
        self.root.geometry("1280x780")
        self.root.minsize(1024, 680)
        self.root.configure(bg=BG)

        apply_theme(self.root)

        # Initialise DB
        try:
            db.initialize_db()
        except ConnectionError as e:
            messagebox.showerror("DB Error", str(e))
            sys.exit(1)

        self.current_user = None
        self.pages = {}

        # Layout
        self._build_layout()
        self.show_login()

    # ── Layout ────────────────────────────────────────────────
    def _build_layout(self):
        # Sidebar (hidden initially)
        self.sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", width=210)
        self.sidebar.pack_propagate(False)

        # Logo area at top of sidebar
        logo_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        logo_frame.pack(fill="x", pady=(20, 10), padx=10)
        tk.Label(logo_frame, text="🌿 EcoMess", bg=SIDEBAR, fg=HIGHLIGHT,
                 font=(FONT, 15, "bold")).pack(anchor="w")
        tk.Label(logo_frame, text="Mess Management System", bg=SIDEBAR,
                 fg=MUTED, font=(FONT, 8)).pack(anchor="w")

        ttk.Separator(self.sidebar).pack(fill="x", padx=10, pady=5)

        # Nav buttons (populated after login)
        self.nav_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.nav_frame.pack(fill="both", expand=True, padx=5)

        # Bottom user info + logout
        self.sidebar_bottom = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.sidebar_bottom.pack(fill="x", side="bottom", pady=10, padx=10)
        ttk.Separator(self.sidebar_bottom).pack(fill="x", pady=(0, 8))
        self.user_label = tk.Label(self.sidebar_bottom, text="", bg=SIDEBAR,
                                   fg=MUTED, font=(FONT, 9), wraplength=180, justify="left")
        self.user_label.pack(anchor="w", pady=(0, 4))
        ttk.Button(self.sidebar_bottom, text="⏻  Logout", style="Red.TButton",
                   command=self._logout).pack(fill="x")

        # Main content area
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(fill="both", expand=True)

    # ── Page Management ───────────────────────────────────────
    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_home(self):
        self._hide_sidebar()
        self._clear_content()
        from home_page import HomePage
        HomePage(self.content, self).pack(fill="both", expand=True)

    def show_login(self):
        self._hide_sidebar()
        self._clear_content()
        from login_page import LoginPage
        LoginPage(self.content, self).pack(fill="both", expand=True)

    def on_login_success(self, user):
        self.current_user = user
        self._show_sidebar()
        self._open_dashboard()

    def _open_dashboard(self):
        self._clear_content()
        role = self.current_user["role"]
        if role == "student":
            from student_dash import StudentDashboard
            StudentDashboard(self.content, self).pack(fill="both", expand=True)
        elif role == "staff":
            from staff_dash import StaffDashboard
            StaffDashboard(self.content, self).pack(fill="both", expand=True)
        elif role == "admin":
            from admin_dash import AdminDashboard
            AdminDashboard(self.content, self).pack(fill="both", expand=True)
        elif role == "kitchen_fpu":
            from kitchen_dash import KitchenDashboard
            KitchenDashboard(self.content, self).pack(fill="both", expand=True)
        elif role == "middleman":
            from middleman_dash import MiddlemanDashboard
            MiddlemanDashboard(self.content, self).pack(fill="both", expand=True)
        elif role in ("ngo", "buyer"):
            from ngo_dash import NgoDashboard
            NgoDashboard(self.content, self).pack(fill="both", expand=True)

    def _logout(self):
        self.current_user = None
        self.show_login()

    # ── Sidebar Helpers ───────────────────────────────────────
    def _show_sidebar(self):
        self.sidebar.pack(side="left", fill="y", before=self.content)
        self._populate_nav()
        name = self.current_user.get("full_name") or self.current_user["username"]
        role = self.current_user["role"].replace("_", " ").title()
        self.user_label.config(text=f"👤 {name}\n{role}")

    def _hide_sidebar(self):
        self.sidebar.pack_forget()

    def _populate_nav(self):
        for w in self.nav_frame.winfo_children():
            w.destroy()

        role = self.current_user["role"]
        if role == "middleman":
            items = [
                ("🌐  Control Tower",     self._open_dashboard),
            ]
        elif role == "student":
            items = [
                ("🏠  Dashboard",     self._open_dashboard),
            ]
        elif role == "staff":
            items = [
                ("🏠  Dashboard",     self._open_dashboard),
            ]
        elif role in ("ngo", "buyer"):
            items = [
                ("🤝  Marketplace",    self._open_dashboard),
            ]
        else:  # admin / kitchen_fpu
            items = [
                ("🏠  Dashboard",     self._open_dashboard),
            ]

        for label, cmd in items:
            btn = tk.Button(
                self.nav_frame, text=label, bg=SIDEBAR, fg=TEXT,
                font=(FONT, 10), bd=0, padx=10, pady=10, anchor="w",
                activebackground=CARD, activeforeground=HIGHLIGHT,
                cursor="hand2", command=cmd, width=22)
            btn.pack(fill="x", pady=1)

    def run(self):
        self.root.mainloop()


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    app = EcoMessApp()
    app.run()
