"""Google Calendar adapter.

Honest v0.1 status: this adapter validates configuration and fails loudly
and clearly when it is missing. Live Google Calendar API calls are the
documented next step (see docs/setup.md for the wiring contract); they are
not silently faked here.

Configuration:
- SLOTFILL_GOOGLE_CREDENTIALS: path to a Google credentials JSON file
  (service account key, or OAuth client credentials), or the standard
  GOOGLE_APPLICATION_CREDENTIALS environment variable.
- SLOTFILL_GOOGLE_CALENDAR_ID: calendar to read and write (default
  "primary").
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from .base import Appointment, CalendarAdapter, CalendarNotConfiguredError

NOT_CONFIGURED_MESSAGE = (
    "Google Calendar is not configured. Set SLOTFILL_GOOGLE_CREDENTIALS to "
    "the path of a Google credentials JSON file (see docs/setup.md), or use "
    "the fake calendar for the offline demo: slotfill demo"
)

NOT_WIRED_MESSAGE = (
    "Google Calendar credentials were found, but live API calls are not "
    "wired in SlotFill v0.1. The adapter contract and the exact calls to "
    "implement are documented in docs/setup.md. No data was read or written."
)


class GoogleCalendarAdapter(CalendarAdapter):
    def __init__(self, credentials_path: str | None = None,
                 calendar_id: str | None = None):
        self.credentials_path = (
            credentials_path
            or os.environ.get("SLOTFILL_GOOGLE_CREDENTIALS")
            or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        )
        self.calendar_id = (
            calendar_id
            or os.environ.get("SLOTFILL_GOOGLE_CALENDAR_ID")
            or "primary"
        )

    def _require_credentials(self) -> Path:
        if not self.credentials_path:
            raise CalendarNotConfiguredError(NOT_CONFIGURED_MESSAGE)
        path = Path(self.credentials_path)
        if not path.exists():
            raise CalendarNotConfiguredError(
                f"Google credentials file not found: {path}. "
                "See docs/setup.md for how to create one."
            )
        return path

    def _require_service(self) -> None:
        self._require_credentials()
        raise NotImplementedError(NOT_WIRED_MESSAGE)

    def list_appointments(self, start: datetime, end: datetime) -> list[Appointment]:
        self._require_service()
        raise AssertionError("unreachable")

    def create_appointment(self, appointment: Appointment) -> Appointment:
        self._require_service()
        raise AssertionError("unreachable")

    def get_cancellations(self) -> list[Appointment]:
        self._require_service()
        raise AssertionError("unreachable")
