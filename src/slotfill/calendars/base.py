"""The calendar adapter contract.

SlotFill is not a booking system. It reads appointments from a calendar the
business already uses, notices cancellations, and writes back exactly one
thing: the replacement appointment when a waitlisted client accepts a freed
slot. Every adapter implements the three methods below.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Appointment:
    id: str
    title: str
    service: str
    start: datetime
    end: datetime
    attendee_name: str = ""
    attendee_contact: str = ""
    status: str = "scheduled"  # scheduled | confirmed | cancelled


class CalendarAdapter(ABC):
    """One small interface every calendar backend must implement."""

    @abstractmethod
    def list_appointments(self, start: datetime, end: datetime) -> list[Appointment]:
        """All non-cancelled appointments starting in [start, end), by start."""

    @abstractmethod
    def create_appointment(self, appointment: Appointment) -> Appointment:
        """Write a new appointment to the calendar. Returns it with its id."""

    @abstractmethod
    def get_cancellations(self) -> list[Appointment]:
        """Appointments cancelled since the last call (each reported once)."""


class CalendarNotConfiguredError(RuntimeError):
    """Raised when an adapter is used without the configuration it needs."""
