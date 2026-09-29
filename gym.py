"""Models, business rules and JSON storage for the Gym Management System."""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any, Optional


class GymError(Exception):
    """Raised for any validation or business-rule violation."""


# plan -> (days, price)
PLANS = {"Monthly": (30, 300.0), "Quarterly": (90, 800.0), "Yearly": (365, 2800.0)}


def _day(v: Any) -> date:
    """ISO string -> date (None -> today)."""
    return date.fromisoformat(v) if isinstance(v, str) else (v or date.today())


# ---------------------------------------------------------------- People ----
class Person(ABC):
    """Abstract base class of Member and Trainer (validated name / phone)."""

    def __init__(self, id: int, name: str, phone: str) -> None:
        self.id = id
        self.name = name      # goes through the validated setters
        self.phone = phone

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, v: str) -> None:
        if not v or not v.strip():
            raise GymError("Name is required.")
        self._name = v.strip()

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, v: str) -> None:
        v = (v or "").strip()
        if not v.isdigit() or not 8 <= len(v) <= 15:
            raise GymError("Phone must be 8-15 digits.")
        self._phone = v

    @abstractmethod
    def label(self) -> str:
        """Text shown in dropdowns (each subclass implements it differently)."""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "phone": self.phone}


class Member(Person):
    def __init__(self, id: int, name: str, phone: str,
                 join_date: Any = None, trainer_id: Optional[int] = None) -> None:
        super().__init__(id, name, phone)
        self.join_date = _day(join_date)
        self.trainer_id = trainer_id

    def label(self) -> str:
        return f"{self.id} - {self.name}"

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "join_date": self.join_date, "trainer_id": self.trainer_id}


class Trainer(Person):
    def __init__(self, id: int, name: str, phone: str, specialty: str = "") -> None:
        super().__init__(id, name, phone)
        self.specialty = specialty.strip() or "General"

    def label(self) -> str:
        return f"{self.id} - {self.name} ({self.specialty})"

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "specialty": self.specialty}


# ------------------------------------------------------- Other entities ----
@dataclass
class Membership:
    id: int
    member_id: int
    plan: str
    start: date
    end: date
    price: float

    def __post_init__(self) -> None:
        self.start, self.end = _day(self.start), _day(self.end)

    @property
    def is_active(self) -> bool:
        return self.start <= date.today() <= self.end


@dataclass
class Payment:
    member_id: int
    amount: float
    note: str = ""
    day: Any = None

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise GymError("Payment amount must be greater than zero.")
        self.day = _day(self.day)


@dataclass
class Attendance:
    member_id: int
    day: Any = None

    def __post_init__(self) -> None:
        self.day = _day(self.day)


# ------------------------------------------------------------------ Gym ----
class Gym:
    """Main class: owns all objects (composition) and enforces business rules."""

    def __init__(self) -> None:
        self._members: dict[int, Member] = {}
        self._trainers: dict[int, Trainer] = {}
        self._memberships: list[Membership] = []
        self._payments: list[Payment] = []
        self._attendance: list[Attendance] = []

    # read-only views (copies)
    @property
    def members(self) -> list[Member]: return list(self._members.values())
    @property
    def trainers(self) -> list[Trainer]: return list(self._trainers.values())
    @property
    def memberships(self) -> list[Membership]: return list(self._memberships)
    @property
    def payments(self) -> list[Payment]: return list(self._payments)
    @property
    def attendance(self) -> list[Attendance]: return list(self._attendance)

    # ----- lookups
    def get_member(self, member_id: int) -> Member:
        if member_id not in self._members:
            raise GymError(f"Member {member_id} does not exist.")
        return self._members[member_id]

    def member_name(self, member_id: int) -> str:
        m = self._members.get(member_id)
        return m.name if m else "(deleted)"

    def trainer_name(self, trainer_id: Optional[int]) -> str:
        t = self._trainers.get(trainer_id)
        return t.name if t else "-"

    # ----- members / trainers
    def add_member(self, name: str, phone: str) -> Member:
        m = Member(max(self._members, default=0) + 1, name, phone)
        self._members[m.id] = m
        return m

    def update_member(self, member_id: int, name: str, phone: str) -> None:
        m = self.get_member(member_id)
        m.name, m.phone = name, phone

    def delete_member(self, member_id: int) -> None:
        self.get_member(member_id)
        del self._members[member_id]
        for attr in ("_memberships", "_payments", "_attendance"):
            setattr(self, attr, [x for x in getattr(self, attr) if x.member_id != member_id])

    def add_trainer(self, name: str, phone: str, specialty: str) -> Trainer:
        t = Trainer(max(self._trainers, default=0) + 1, name, phone, specialty)
        self._trainers[t.id] = t
        return t

    def assign_trainer(self, member_id: int, trainer_id: int) -> None:
        member = self.get_member(member_id)
        if trainer_id not in self._trainers:
            raise GymError(f"Trainer {trainer_id} does not exist.")
        member.trainer_id = trainer_id

    # ----- memberships
    def active_membership(self, member_id: int) -> Optional[Membership]:
        return next((s for s in self._memberships
                     if s.member_id == member_id and s.is_active), None)

    def status_of(self, member_id: int) -> str:
        if self.active_membership(member_id):
            return "Active"
        if any(s.member_id == member_id for s in self._memberships):
            return "Expired"
        return "No Membership"

    @staticmethod
    def _plan(plan: str) -> tuple[int, float]:
        if plan not in PLANS:
            raise GymError("Please choose a valid plan.")
        return PLANS[plan]

    def create_membership(self, member_id: int, plan: str) -> Membership:
        self.get_member(member_id)
        days, price = self._plan(plan)
        if self.active_membership(member_id):
            raise GymError("This member already has an active membership.")
        start = date.today()
        ms = Membership(max((s.id for s in self._memberships), default=0) + 1,
                        member_id, plan, start, start + timedelta(days=days), price)
        self._memberships.append(ms)
        self.record_payment(member_id, price, f"{plan} membership")
        return ms

    def renew_membership(self, member_id: int, plan: str) -> Membership:
        self.get_member(member_id)
        days, price = self._plan(plan)
        current = self.active_membership(member_id)
        if current is None:                       # expired / none -> new one
            return self.create_membership(member_id, plan)
        current.end += timedelta(days=days)       # still active -> extend
        self.record_payment(member_id, price, f"{plan} renewal")
        return current

    # ----- payments & attendance
    def record_payment(self, member_id: int, amount: float, note: str = "") -> Payment:
        self.get_member(member_id)
        p = Payment(member_id, amount, note)
        self._payments.append(p)
        return p

    def record_attendance(self, member_id: int) -> Attendance:
        self.get_member(member_id)
        if not self.active_membership(member_id):
            raise GymError("Cannot attend: membership is expired or missing.")
        a = Attendance(member_id)
        self._attendance.append(a)
        return a

    # ----- search / dashboard
    def search_members(self, text: str = "", status: str = "All") -> list[Member]:
        text = text.strip().lower()
        return [m for m in self._members.values()
                if (not text or text in m.name.lower() or text in m.phone or text == str(m.id))
                and (status == "All" or self.status_of(m.id) == status)]

    def dashboard(self) -> dict[str, Any]:
        st = [self.status_of(m.id) for m in self._members.values()]
        today = date.today()
        return {
            "Total Members": len(self._members),
            "Total Trainers": len(self._trainers),
            "Active Memberships": st.count("Active"),
            "Expired Memberships": st.count("Expired"),
            "Total Revenue": f"{sum(p.amount for p in self._payments):.2f}",
            "Today's Attendance": sum(a.day == today for a in self._attendance),
        }

    # ----- persistence
    def to_dict(self) -> dict[str, Any]:
        return {
            "members": [m.to_dict() for m in self._members.values()],
            "trainers": [t.to_dict() for t in self._trainers.values()],
            "memberships": [asdict(x) for x in self._memberships],
            "payments": [asdict(x) for x in self._payments],
            "attendance": [asdict(x) for x in self._attendance],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Gym:
        gym = cls()
        try:
            gym._members = {d["id"]: Member(**d) for d in data.get("members", [])}
            gym._trainers = {d["id"]: Trainer(**d) for d in data.get("trainers", [])}
            gym._memberships = [Membership(**d) for d in data.get("memberships", [])]
            gym._payments = [Payment(**d) for d in data.get("payments", [])]
            gym._attendance = [Attendance(**d) for d in data.get("attendance", [])]
        except (KeyError, ValueError, TypeError) as e:
            raise GymError(f"Data file is corrupted: {e}")
        return gym


# ---------------------------------------------------------- FileManager ----
class FileManager:
    """Reads / writes the JSON file (kept separate from business logic)."""

    def __init__(self, path: str) -> None:
        self._path = path

    def load(self) -> dict[str, Any]:
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise GymError(f"Could not read data file: {e}")

    def save(self, data: dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)   # dates -> ISO strings
        except OSError as e:
            raise GymError(f"Could not save data file: {e}")
