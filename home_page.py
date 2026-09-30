"""
home_page.py — EcoMess Landing / Home Page
Shown before login. Describes the project.
"""

import tkinter as tk
from tkinter import ttk

BG       = "#1b2228"
CARD     = "#1f3040"
ACCENT   = "#2d6a4f"
ACCENT2  = "#40916c"
HIGHLIGHT= "#74c69d"
TEXT     = "#edf2f4"
MUTED    = "#94a3b8"
FONT     = "Segoe UI"


class HomePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        # ── Hero Section ──────────────────────────────────────
        hero = tk.Frame(self, bg=ACCENT, height=280)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        inner = tk.Frame(hero, bg=ACCENT)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(inner, text="🌿", bg=ACCENT, font=(FONT, 52)).pack()
        tk.Label(inner, text="EcoMess", bg=ACCENT, fg=TEXT,
                 font=(FONT, 38, "bold")).pack()
        tk.Label(inner, text="Smart Mess Management System",
                 bg=ACCENT, fg="#d8f3dc", font=(FONT, 14)).pack(pady=(4, 0))

        # ── About Card ────────────────────────────────────────
        about_frame = tk.Frame(self, bg=BG)
        about_frame.pack(fill="both", expand=True, padx=60, pady=30)

        tk.Label(about_frame, text="About EcoMess", bg=BG, fg=HIGHLIGHT,
                 font=(FONT, 16, "bold")).pack(anchor="w", pady=(0, 8))

        desc = (
            "EcoMess is a comprehensive digital mess management system designed for colleges "
            "and institutions. It streamlines daily mess operations by connecting three key "
            "stakeholders — Students, Staff, and Administrators — through a unified platform.\n\n"
            "Students can view their weekly menu, pay mess fees, vote on tomorrow's food, "
            "and submit complaints. Staff members can track inventory, log food wastage, "
            "and check their salary details. Administrators have full control: managing "
            "users, editing menus, viewing reports on food waste, and sending notifications "
            "to students and staff.\n\n"
            "EcoMess reduces food waste, improves transparency, and creates a better "
            "experience for everyone in the mess ecosystem. 🌱"
        )
        tk.Label(about_frame, text=desc, bg=BG, fg=TEXT,
                 font=(FONT, 11), wraplength=900, justify="left").pack(anchor="w", pady=(0, 20))

        # ── Feature Cards ─────────────────────────────────────
        cards_frame = tk.Frame(about_frame, bg=BG)
        cards_frame.pack(fill="x", pady=(0, 20))

        features = [
            ("🎓", "Students",     "Menu, fee payment,\npoll & complaints."),
            ("👨‍🍳", "Staff",       "Inventory, salary\n& food waste tracking."),
            ("🛡️", "Admin",       "Full control: users, menu,\nreports & notifications."),
        ]

        for icon, title, detail in features:
            card = tk.Frame(cards_frame, bg=CARD, bd=0, relief="flat")
            card.pack(side="left", expand=True, fill="both", padx=8, pady=4, ipadx=16, ipady=16)
            tk.Label(card, text=icon,   bg=CARD, fg=TEXT,     font=(FONT, 28)).pack(pady=(8,0))
            tk.Label(card, text=title,  bg=CARD, fg=HIGHLIGHT, font=(FONT, 12, "bold")).pack()
            tk.Label(card, text=detail, bg=CARD, fg=MUTED,     font=(FONT, 9),
                     justify="center").pack(pady=(4, 8))

        # ── Login Button ──────────────────────────────────────
        btn = tk.Button(about_frame, text="  Login to EcoMess  →",
                        bg=ACCENT2, fg=TEXT, font=(FONT, 12, "bold"),
                        bd=0, padx=24, pady=10, cursor="hand2",
                        activebackground=HIGHLIGHT, activeforeground=BG,
                        command=self.app.show_login)
        btn.pack(pady=4)
