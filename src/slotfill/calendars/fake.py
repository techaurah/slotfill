"""A fully working in-memory calendar, used by the demo and the test suite.

It behaves like a real adapter (including cancellation reporting), so the
whole SlotFill pipeline can be exercised offline with zero credentials.
"""

from __future__ import annotations

from datetime import datetime

from .base import Appointment, CalendarAdapter


class FakeCalendar(CalendarAdapter):
    def __init__(self, appointments: list[Appointment] | None = None):
        self._appointments: dict[str, Appointment] = {}
        self._pending_cancellations: list[Appointment] = []
        self._counter = 0
        for appt in appointments or []:
            self.add_appointment(appt)

    def add_appointment(self, appointment: Appointment) -> Appointment:
        if not appointment.id:
            self._counter += 1
            appointment.id = f"fake-{self._counter}"
        self._appointments[appointment.id] = appointment
        return appointment

    def get_appointment(self, appointment_id: str) -> Appointment | None:
        return self._appointments.get(appointment_id)

    def cancel_appointment(self, appointment_id: str) -> Appointment:
        """Simulate the business (or client) cancelling an appointment."""
        appt = self._appointments[appointment_id]
        appt.status = "cancelled"
        self._pending_cancellations.append(appt)
        return appt

    def list_appointments(self, start: datetime, end: datetime) -> list[Appointment]:
        return sorted(
            (
                a
                for a in self._appointments.values()
                if a.status != "cancelled" and start <= a.start < end
            ),
            key=lambda a: a.start,
        )

    def create_appointment(self, appointment: Appointment) -> Appointment:
        appointment.id = ""
        return self.add_appointment(appointment)

    def get_cancellations(self) -> list[Appointment]:
        out, self._pending_cancellations = self._pending_cancellations, []
        return out
