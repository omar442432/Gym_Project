"""Tkinter GUI for the Gym Management System.  Run:  python main.py

Visual theme: dark / high-contrast, black + ember-orange, built for a gym brand.
All business logic lives in gym.py — this file only renders and wires the UI.
"""
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from gym import PLANS, FileManager, Gym, GymError

# ----------------------------------------------------------------- palette --
BG = "#111214"        # app background
PANEL = "#18191C"     # tab body background
CARD = "#1D1E23"      # cards / table background
CARD_ALT = "#24252B"  # inputs, alt rows, hover
BORDER = "#2C2D34"
ACCENT = "#FF4B26"     # ember orange-red
ACCENT_DARK = "#C7350F"
ACCENT_SOFT = "#3A241C"
DANGER = "#FF5B4D"
DANGER_BG = "#3A1B18"
TEXT = "#F3F4F6"
MUTED = "#9BA0AA"


def _pick_font() -> str:
    families = set(tkfont.families())
    for f in ("Segoe UI", "Helvetica Neue", "Helvetica", "Arial"):
        if f in families:
            return f
    return "TkDefaultFont"


class GymApp(tk.Tk):
    def __init__(self, gym: Gym, fm: FileManager) -> None:
        super().__init__()
        self.title("Gym Management System")
        self.geometry("1040x660")
        self.minsize(960, 600)
        self.configure(bg=BG)
        self.gym, self.fm = gym, fm
        self.FONT = _pick_font()

        self._apply_theme()
        self._build_header()

        self.nb = ttk.Notebook(self, style="Gym.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=18, pady=(4, 18))
        self.trees, self.member_boxes = {}, []

        self.dash = self._tab("Dashboard")
        self._members_tab()
        self._trainers_tab()
        self._memberships_tab()
        self._payments_tab()
        self._attendance_tab()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- theme --
    def _apply_theme(self) -> None:
        F = self.FONT
        self.option_add("*Font", (F, 10))
        self.option_add("*TCombobox*Listbox.background", CARD_ALT)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        self.option_add("*TCombobox*Listbox.borderWidth", 0)

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=TEXT, font=(F, 10))
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Card.TFrame", background=CARD)

        style.configure("TLabel", background=BG, foreground=TEXT, font=(F, 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=(F, 10))
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=(F, 9))
        style.configure("Eyebrow.TLabel", background=BG, foreground=ACCENT, font=(F, 10, "bold"))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=(F, 18, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=(F, 10))

        # entries
        style.configure("TEntry", fieldbackground=CARD_ALT, foreground=TEXT,
                         insertcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER,
                         darkcolor=BORDER, borderwidth=1, padding=7, relief="flat")
        style.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)],
                  darkcolor=[("focus", ACCENT)])

        # combobox
        style.configure("TCombobox", fieldbackground=CARD_ALT, background=CARD_ALT,
                         foreground=TEXT, arrowcolor=ACCENT, bordercolor=BORDER,
                         lightcolor=BORDER, darkcolor=BORDER, borderwidth=1, padding=6,
                         relief="flat")
        style.map("TCombobox",
                  fieldbackground=[("readonly", CARD_ALT), ("focus", CARD_ALT)],
                  foreground=[("readonly", TEXT)],
                  bordercolor=[("focus", ACCENT)])

        # buttons
        style.configure("TButton", background=CARD_ALT, foreground=TEXT, borderwidth=0,
                         focuscolor=CARD_ALT, padding=(14, 8), font=(F, 10, "bold"))
        style.map("TButton", background=[("active", BORDER)])

        style.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF",
                         borderwidth=0, focuscolor=ACCENT, padding=(16, 9), font=(F, 10, "bold"))
        style.map("Accent.TButton", background=[("active", ACCENT_DARK)])

        style.configure("Danger.TButton", background=DANGER_BG, foreground=DANGER,
                         borderwidth=0, focuscolor=DANGER_BG, padding=(14, 8), font=(F, 10, "bold"))
        style.map("Danger.TButton", background=[("active", "#4A211D")])

        # notebook / tabs
        style.configure("Gym.TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0),
                         bordercolor=BG, darkcolor=BG, lightcolor=BG)
        style.configure("Gym.TNotebook.Tab", background=BG, foreground=MUTED,
                         padding=(18, 11), font=(F, 10, "bold"), borderwidth=0)
        style.map("Gym.TNotebook.Tab",
                  background=[("selected", PANEL)],
                  foreground=[("selected", ACCENT)])
        style.layout("Gym.TNotebook", [("Notebook.client", {"sticky": "nswe"})])

        # treeview
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                         rowheight=30, borderwidth=0, font=(F, 10))
        style.configure("Treeview.Heading", background=CARD_ALT, foreground=ACCENT,
                         font=(F, 9, "bold"), borderwidth=0, relief="flat", padding=(10, 8))
        style.map("Treeview.Heading", background=[("active", CARD_ALT)])
        style.map("Treeview", background=[("selected", ACCENT)],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # ------------------------------------------------------------ header --
    def _build_header(self) -> None:
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=18, pady=(16, 6))

        mark = tk.Frame(bar, bg=ACCENT, width=42, height=42)
        mark.pack(side="left")
        mark.pack_propagate(False)
        tk.Label(mark, text="\U0001F3CB", bg=ACCENT, fg="#FFFFFF",
                 font=(self.FONT, 17)).place(relx=0.5, rely=0.48, anchor="center")

        text_col = tk.Frame(bar, bg=BG)
        text_col.pack(side="left", padx=(12, 0))
        ttk.Label(text_col, text="GYM MANAGEMENT SYSTEM", style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(text_col, text="Members \u00b7 Trainers \u00b7 Memberships \u00b7 Payments",
                  style="Sub.TLabel").pack(anchor="w")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=18)

    # ------------------------------------------------------------ helpers --
    def _tab(self, name: str) -> tk.Frame:
        f = tk.Frame(self.nb, bg=PANEL)
        self.nb.add(f, text=f"  {name}  ")
        return f

    def _row(self, parent: tk.Misc) -> tk.Frame:
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=20, pady=10)
        return f

    def _table(self, parent: tk.Misc, key: str, cols: tuple[str, ...]) -> ttk.Treeview:
        wrap = tk.Frame(parent, bg=BORDER)
        wrap.pack(fill="both", expand=True, padx=20, pady=(4, 10))
        inner = tk.Frame(wrap, bg=CARD)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tree = ttk.Treeview(inner, columns=cols, show="headings", height=9)
        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=110)
        tree.pack(fill="both", expand=True, padx=1, pady=1)
        tree.tag_configure("odd", background=CARD_ALT)
        tree.tag_configure("even", background=CARD)
        self.trees[key] = tree
        return tree

    def _entry(self, row: tk.Misc, label: str, width: int = 16) -> tk.StringVar:
        var = tk.StringVar()
        ttk.Label(row, text=label, style="Panel.TLabel").pack(side="left", padx=(0, 6))
        ttk.Entry(row, textvariable=var, width=width).pack(side="left", padx=(0, 16))
        return var

    def _box(self, row: tk.Misc, values=(), width: int = 28) -> ttk.Combobox:
        box = ttk.Combobox(row, values=list(values), state="readonly", width=width)
        box.pack(side="left", padx=(0, 16))
        return box

    def _member_box(self, row: tk.Misc) -> ttk.Combobox:
        ttk.Label(row, text="Member", style="Panel.TLabel").pack(side="left", padx=(0, 6))
        box = self._box(row)
        self.member_boxes.append(box)
        return box

    def _button(self, row: tk.Misc, text: str, action, msg: str = "", kind: str = "") -> None:
        style = {"accent": "Accent.TButton", "danger": "Danger.TButton"}.get(kind, "TButton")
        ttk.Button(row, text=text, style=style,
                   command=lambda: self._do(action, msg)).pack(side="left", padx=(0, 8))

    @staticmethod
    def _id(box: ttk.Combobox) -> int:
        """'3 - Ahmed' -> 3"""
        if not box.get():
            raise GymError("Please select an item from the list.")
        return int(box.get().split(" - ")[0])

    def _selected(self) -> int:
        sel = self.trees["members"].selection()
        if not sel:
            raise GymError("Select a member from the table first.")
        return int(self.trees["members"].item(sel[0])["values"][0])

    def _do(self, action, msg: str = "") -> None:
        """Run action -> save -> refresh -> message. GymError -> error box."""
        try:
            if action() is False:          # action cancelled by the user
                return
            self.fm.save(self.gym.to_dict())
            self.refresh()
            if msg:
                messagebox.showinfo("Done", msg)
        except GymError as e:
            messagebox.showerror("Error", str(e))

    @staticmethod
    def _amount(text: str) -> float:
        try:
            return float(text)
        except ValueError:
            raise GymError("Amount must be a number.")

    # --------------------------------------------------------------- tabs --
    def _members_tab(self) -> None:
        t, g = self._tab("Members"), self.gym
        top = self._row(t)
        self.search = self._entry(top, "Search", 20)
        self.status = tk.StringVar(value="All")
        ttk.Label(top, text="Status", style="Panel.TLabel").pack(side="left", padx=(0, 6))
        ttk.Combobox(top, textvariable=self.status, state="readonly", width=14,
                     values=["All", "Active", "Expired", "No Membership"]).pack(side="left", padx=(0, 16))
        self._button(top, "Search / Filter", self.refresh, kind="accent")

        tree = self._table(t, "members", ("ID", "Name", "Phone", "Status", "Trainer"))
        tree.bind("<<TreeviewSelect>>", self._on_select)

        form = self._row(t)
        self.name, self.phone = self._entry(form, "Name", 20), self._entry(form, "Phone")
        self._button(form, "Add", lambda: g.add_member(self.name.get(), self.phone.get()),
                     "Member added.", "accent")
        self._button(form, "Update", lambda: g.update_member(self._selected(), self.name.get(),
                                                             self.phone.get()), "Member updated.")
        self._button(form, "Delete", self._delete, "Member deleted.", "danger")

        assign = self._row(t)
        ttk.Label(assign, text="Assign trainer to selected member", style="Panel.TLabel").pack(side="left", padx=(0, 8))
        self.trainer_box = self._box(assign, width=30)
        self._button(assign, "Assign", lambda: g.assign_trainer(self._selected(), self._id(self.trainer_box)),
                     "Trainer assigned.", "accent")

    def _on_select(self, _e) -> None:
        try:
            m = self.gym.get_member(self._selected())   # read from model (keeps leading zeros)
            self.name.set(m.name)
            self.phone.set(m.phone)
        except GymError:
            pass

    def _delete(self):
        if not messagebox.askyesno("Confirm", "Delete the selected member and all their records?"):
            return False
        self.gym.delete_member(self._selected())

    def _trainers_tab(self) -> None:
        t, g = self._tab("Trainers"), self.gym
        self._table(t, "trainers", ("ID", "Name", "Phone", "Specialty"))
        form = self._row(t)
        n, p, s = self._entry(form, "Name", 18), self._entry(form, "Phone"), self._entry(form, "Specialty")
        self._button(form, "Add Trainer", lambda: g.add_trainer(n.get(), p.get(), s.get()),
                     "Trainer added.", "accent")

    def _memberships_tab(self) -> None:
        t, g = self._tab("Memberships"), self.gym
        top = self._row(t)
        box = self._member_box(top)
        ttk.Label(top, text="Plan", style="Panel.TLabel").pack(side="left", padx=(0, 6))
        plan = self._box(top, PLANS, 12)
        plan.set("Monthly")
        self._button(top, "Create", lambda: g.create_membership(self._id(box), plan.get()),
                     "Membership created (payment recorded).", "accent")
        self._button(top, "Renew", lambda: g.renew_membership(self._id(box), plan.get()),
                     "Membership renewed (payment recorded).")
        self._table(t, "memberships", ("ID", "Member", "Plan", "Start", "End", "Price", "Status"))

    def _payments_tab(self) -> None:
        t, g = self._tab("Payments"), self.gym
        top = self._row(t)
        box = self._member_box(top)
        amount = self._entry(top, "Amount", 10)
        self._button(top, "Record Payment",
                     lambda: g.record_payment(self._id(box), self._amount(amount.get())),
                     "Payment recorded.", "accent")
        self._table(t, "payments", ("Member", "Amount", "Date", "Note"))

    def _attendance_tab(self) -> None:
        t, g = self._tab("Attendance"), self.gym
        top = self._row(t)
        box = self._member_box(top)
        self._button(top, "Check In", lambda: g.record_attendance(self._id(box)),
                     "Attendance recorded.", "accent")
        self._table(t, "attendance", ("Member", "Date"))

    # ------------------------------------------------------------ refresh --
    def _fill(self, key: str, rows: list[tuple]) -> None:
        tree = self.trees[key]
        tree.delete(*tree.get_children())
        for i, r in enumerate(rows):
            tree.insert("", "end", values=r, tags=("odd" if i % 2 else "even",))

    def refresh(self) -> None:
        g = self.gym
        for w in self.dash.winfo_children():
            w.destroy()
        self._build_dashboard(g.dashboard())

        self._fill("members", [(m.id, m.name, m.phone, g.status_of(m.id), g.trainer_name(m.trainer_id))
                               for m in g.search_members(self.search.get(), self.status.get())])
        self._fill("trainers", [(t.id, t.name, t.phone, t.specialty) for t in g.trainers])
        self._fill("memberships", [(s.id, g.member_name(s.member_id), s.plan, s.start, s.end, s.price,
                                    "Active" if s.is_active else "Expired") for s in g.memberships])
        self._fill("payments", [(g.member_name(p.member_id), f"{p.amount:.2f}", p.day, p.note)
                                for p in g.payments])
        self._fill("attendance", [(g.member_name(a.member_id), a.day) for a in g.attendance])

        for box in self.member_boxes:                    # polymorphism: label()
            box["values"] = [m.label() for m in g.members]
        self.trainer_box["values"] = [t.label() for t in g.trainers]

    def _build_dashboard(self, data: dict) -> None:
        wrap = tk.Frame(self.dash, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=20, pady=20)
        icons = ["\U0001F465", "\U0001F3CB", "\u2705", "\u26A0", "\U0001F4B0", "\U0001F4C5"]
        for i, (label, value) in enumerate(data.items()):
            outer = tk.Frame(wrap, bg=BORDER)
            outer.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")
            card = tk.Frame(outer, bg=CARD, padx=20, pady=18)
            card.pack(padx=1, pady=1, fill="both", expand=True)

            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x")
            badge = tk.Frame(top, bg=ACCENT_SOFT, width=34, height=34)
            badge.pack(side="left")
            badge.pack_propagate(False)
            tk.Label(badge, text=icons[i % len(icons)], bg=ACCENT_SOFT, fg=ACCENT,
                     font=(self.FONT, 13)).place(relx=0.5, rely=0.48, anchor="center")

            tk.Label(card, text=str(value), bg=CARD, fg=TEXT,
                     font=(self.FONT, 26, "bold")).pack(anchor="w", pady=(14, 0))
            tk.Label(card, text=label.upper(), bg=CARD, fg=MUTED,
                     font=(self.FONT, 9, "bold")).pack(anchor="w", pady=(2, 0))
        for c in range(3):
            wrap.grid_columnconfigure(c, weight=1, uniform="dash")

    def _on_close(self) -> None:
        try:
            self.fm.save(self.gym.to_dict())
        except GymError as e:
            messagebox.showerror("Error", str(e))
        self.destroy()


def main() -> None:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "gym.json")
    fm = FileManager(path)
    try:
        gym = Gym.from_dict(fm.load())
    except GymError as e:
        print(e)
        gym = Gym()
    GymApp(gym, fm).mainloop()


if __name__ == "__main__":
    main()
