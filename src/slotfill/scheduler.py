"""The SlotFill service: one cycle of reminders, expiries and backfill."""

from __future__ import annotations

from datetime import datetime, timedelta

from .backfill import BackfillEngine
from .calendars.base import CalendarAdapter
from .config import Pack
from .notify.base import Notifier
from .reminders import ReminderEngine, classify_reply, format_start, render_template
from .store import StateStore
from .waitlist import WaitlistEntry


class SlotfillService:
    def __init__(self, calendar: CalendarAdapter, entries: list[WaitlistEntry],
                 pack: Pack, notifier: Notifier, store: StateStore,
                 business_name: str = "Your Business"):
        self.calendar = calendar
        self.pack = pack
        self.notifier = notifier
        self.store = store
        self.business_name = business_name
        self.reminders = ReminderEngine(pack, notifier, store, business_name)
        self.backfill = BackfillEngine(
            calendar, entries, pack, notifier, store, business_name
        )

    def run_cycle(self, now: datetime, window_days: int = 7) -> dict:
        """Run one full cycle at time `now`. Safe to call on any schedule:
        reminders and cancellations are each processed exactly once.
        """
        appointments = self.calendar.list_appointments(
            now - timedelta(days=1), now + timedelta(days=window_days)
        )
        reminders_sent = self.reminders.run(appointments, now)
        expired = self.backfill.expire_offers(now)
        cancellations = self.calendar.get_cancellations()
        offers: list[dict] = []
        for cancelled in cancellations:
            offers.extend(self.backfill.handle_cancellation(cancelled, now))
        return {
            "reminders_sent": len(reminders_sent),
            "offers_expired": expired,
            "cancellations": len(cancellations),
            "offers_created": len(offers),
        }

    def handle_reply(self, contact: str, text: str, now: datetime) -> str:
        """Route one inbound reply. Returns a short action code describing
        what happened, for logging by the caller.
        """
        action = classify_reply(text, self.pack)
        if action == "confirm":
            appt = self.backfill.accept(contact, now)
            if appt is not None:
                return f"backfill_accepted:{appt.id}"
            upcoming = [
                a
                for a in self.calendar.list_appointments(
                    now, now + timedelta(days=30)
                )
                if a.attendee_contact == contact
            ]
            if upcoming:
                self.store.mark_confirmed(upcoming[0].id)
                body = render_template(
                    self.pack.template("confirm_ack"),
                    name=upcoming[0].attendee_name or "there",
                    service=upcoming[0].service,
                    start=format_start(upcoming[0].start),
                    business=self.business_name,
                )
                subject = f"Confirmed: {upcoming[0].service} on {format_start(upcoming[0].start)}"
                self.notifier.send(contact, subject, body, kind="confirm_ack")
                self.store.log_send("confirm_ack", contact, subject, body, now)
                return f"appointment_confirmed:{upcoming[0].id}"
            return "confirm_no_match"
        if action == "reschedule":
            if self.store.pending_offer_for_contact(contact) is not None:
                self.backfill.decline(contact, now)
            body = render_template(
                self.pack.template("reschedule_ack"),
                name="there",
                service="",
                start="",
                business=self.business_name,
            )
            subject = "Reschedule request received"
            self.notifier.send(contact, subject, body, kind="reschedule_ack")
            self.store.log_send("reschedule_ack", contact, subject, body, now)
            return "reschedule_requested"
        return "unrecognised"
