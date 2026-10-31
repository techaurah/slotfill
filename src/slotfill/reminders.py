"""Reminder engine and reply classification.

Fully deterministic: offsets, templates and keywords come from the vertical
pack, sends are deduplicated through the state store, and there is no LLM
anywhere in the loop.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from .calendars.base import Appointment
from .config import Pack, SlotfillError
from .notify.base import Notifier, SentMessage
from .store import StateStore

_OFFSET_RE = re.compile(r"^\s*(\d+)\s*(m|min|h|hr|d|day|days)\s*$", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z']+")


def parse_offset(offset: str) -> timedelta:
    """Parse pack offsets like '30m', '2h', '48h', '1d' into a timedelta."""
    match = _OFFSET_RE.match(offset or "")
    if not match:
        raise SlotfillError(
            f"Unparseable reminder offset: {offset!r} (use forms like 30m, 2h, 1d)"
        )
    value, unit = int(match.group(1)), match.group(2).lower()
    if unit in ("m", "min"):
        return timedelta(minutes=value)
    if unit in ("h", "hr"):
        return timedelta(hours=value)
    return timedelta(days=value)


def format_start(dt: datetime) -> str:
    return dt.strftime("%a %d %b %Y at %H:%M")


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


def render_template(template: str, **context: object) -> str:
    return template.format_map(_SafeDict({k: str(v) for k, v in context.items()}))


def classify_reply(text: str, pack: Pack) -> str | None:
    """Classify a client reply using the pack's keywords.

    Returns "reschedule", "confirm", or None. Reschedule is checked first so
    a message like "change it, yes" is treated as a move request, not a
    confirmation.
    """
    lowered = (text or "").lower()
    tokens = set(_WORD_RE.findall(lowered))

    def hit(keyword: str) -> bool:
        return keyword in tokens or ((" " in keyword) and keyword in lowered)

    if any(hit(k) for k in pack.reschedule_keywords):
        return "reschedule"
    if any(hit(k) for k in pack.confirm_keywords):
        return "confirm"
    return None


class ReminderEngine:
    def __init__(self, pack: Pack, notifier: Notifier, store: StateStore,
                 business_name: str = "Your Business",
                 grace: timedelta = timedelta(hours=1)):
        self.pack = pack
        self.notifier = notifier
        self.store = store
        self.business_name = business_name
        # A reminder fires inside a catch-up window after its fire time, so a
        # service restarting after downtime sends the current reminder, not a
        # blast of every reminder whose time passed while it was down.
        self.grace = grace

    def due(self, appointments: list[Appointment],
            now: datetime) -> list[tuple[Appointment, str]]:
        """(appointment, offset) pairs whose reminder should fire at `now`."""
        out: list[tuple[Appointment, str]] = []
        for appt in appointments:
            if appt.status == "cancelled":
                continue
            for rule in self.pack.reminders:
                fire_at = appt.start - parse_offset(rule.offset)
                if (
                    fire_at <= now <= fire_at + self.grace
                    and now < appt.start
                    and not self.store.was_reminder_sent(appt.id, rule.offset)
                ):
                    out.append((appt, rule.offset))
        return out

    def run(self, appointments: list[Appointment],
            now: datetime) -> list[SentMessage]:
        sent: list[SentMessage] = []
        template_by_offset = {r.offset: r.template for r in self.pack.reminders}
        for appt, offset in self.due(appointments, now):
            body = render_template(
                self.pack.template(template_by_offset[offset]),
                name=appt.attendee_name or "there",
                service=appt.service,
                start=format_start(appt.start),
                business=self.business_name,
                offset=offset,
            )
            subject = f"Reminder: {appt.service} on {format_start(appt.start)}"
            msg = self.notifier.send(
                appt.attendee_contact, subject, body, kind="reminder"
            )
            self.store.log_send("reminder", appt.attendee_contact, subject, body, now)
            self.store.mark_reminder_sent(appt.id, offset, now)
            sent.append(msg)
        return sent
