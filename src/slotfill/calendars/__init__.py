"""Calendar adapters: one interface, several backends."""

from .base import Appointment, CalendarAdapter, CalendarNotConfiguredError
from .caldav import CalDAVCalendarAdapter
from .fake import FakeCalendar
from .google import GoogleCalendarAdapter

__all__ = [
    "Appointment",
    "CalendarAdapter",
    "CalendarNotConfiguredError",
    "CalDAVCalendarAdapter",
    "FakeCalendar",
    "GoogleCalendarAdapter",
]
