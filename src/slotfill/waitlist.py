"""CSV waitlist loading and slot matching.

The waitlist is deliberately a CSV file in v0.1: every appointment business
can export or type one, and a human can read exactly who will be asked about
a freed slot before anything runs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import SlotfillError


@dataclass
class WaitlistEntry:
    name: str
    contact: str
    service: str
    earliest: datetime | None = None
    latest: datetime | None = None
    position: int = 0  # row order in the CSV: first come, first offered

    def matches(self, service: str, start: datetime, end: datetime) -> bool:
        """True if this entry wants `service` and the slot fits its window."""
        if self.service and self.service.strip().lower() != service.strip().lower():
            return False
        if self.earliest is not None and start < self.earliest:
            return False
        if self.latest is not None and end > self.latest:
            return False
        return True


def _parse_dt(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise SlotfillError(f"Bad datetime in waitlist CSV: {value!r}") from exc


def load_waitlist(path: str | Path) -> list[WaitlistEntry]:
    """Load waitlist entries from a CSV with columns:
    name, contact, service, earliest, latest. Order is preserved.
    """
    path = Path(path)
    if not path.exists():
        raise SlotfillError(f"Waitlist file not found: {path}")
    entries: list[WaitlistEntry] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"name", "contact", "service"}
        if reader.fieldnames is None or not required.issubset(
            {f.strip() for f in reader.fieldnames}
        ):
            raise SlotfillError(
                f"Waitlist CSV {path} must have columns: name, contact, service,"
                " earliest, latest"
            )
        for i, row in enumerate(reader):
            name = (row.get("name") or "").strip()
            contact = (row.get("contact") or "").strip()
            if not name or not contact:
                continue
            entries.append(
                WaitlistEntry(
                    name=name,
                    contact=contact,
                    service=(row.get("service") or "").strip(),
                    earliest=_parse_dt(row.get("earliest") or ""),
                    latest=_parse_dt(row.get("latest") or ""),
                    position=i,
                )
            )
    return entries


def matching_entries(entries: list[WaitlistEntry], service: str,
                     start: datetime, end: datetime) -> list[WaitlistEntry]:
    """All entries matching a freed slot, in waitlist order."""
    return [e for e in entries if e.matches(service, start, end)]
