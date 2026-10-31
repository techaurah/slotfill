"""CalDAV calendar adapter: documented stub.

Contract for whoever implements this adapter (a good second contribution):

- Configuration: SLOTFILL_CALDAV_URL (collection URL), SLOTFILL_CALDAV_USER,
  SLOTFILL_CALDAV_PASSWORD.
- list_appointments(start, end): fetch VEVENTs in the window with a CalDAV
  time-range REPORT, skip STATUS:CANCELLED events, map SUMMARY to title,
  DTSTART/DTEND to start/end, and the attendee email (ATTENDEE mailto:) to
  attendee_contact. The service name comes from a configurable VEVENT
  property or category (decide and document it in docs/setup.md).
- create_appointment(appointment): PUT a new VEVENT with a fresh UID and
  return the appointment with that UID as its id.
- get_cancellations(): CalDAV has no push feed, so poll: keep the last sync
  token (or last-seen ETags) and report events that disappeared or gained
  STATUS:CANCELLED since the previous call. Each cancellation is reported
  exactly once.

Until implemented, every method raises NotImplementedError rather than
pretending to work.
"""

from __future__ import annotations

import os
from datetime import datetime

from .base import Appointment, CalendarAdapter

STUB_MESSAGE = (
    "The CalDAV adapter is a documented stub in SlotFill v0.1 and does not "
    "read or write any calendar yet. The implementation contract is in "
    "src/slotfill/calendars/caldav.py and docs/setup.md. Use the fake "
    "calendar (slotfill demo) or the Google adapter configuration in the "
    "meantime."
)


class CalDAVCalendarAdapter(CalendarAdapter):
    def __init__(self, url: str | None = None, username: str | None = None,
                 password: str | None = None):
        self.url = url or os.environ.get("SLOTFILL_CALDAV_URL", "")
        self.username = username or os.environ.get("SLOTFILL_CALDAV_USER", "")
        self.password = password or os.environ.get("SLOTFILL_CALDAV_PASSWORD", "")

    def list_appointments(self, start: datetime, end: datetime) -> list[Appointment]:
        raise NotImplementedError(STUB_MESSAGE)

    def create_appointment(self, appointment: Appointment) -> Appointment:
        raise NotImplementedError(STUB_MESSAGE)

    def get_cancellations(self) -> list[Appointment]:
        raise NotImplementedError(STUB_MESSAGE)
