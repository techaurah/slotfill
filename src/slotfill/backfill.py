"""The waitlist backfill state machine.

When an appointment is cancelled:

1. The freed slot is matched against the waitlist, in order (service and
   acceptable time window must fit).
2. The first matches (up to the pack's max_offers) each receive an offer
   with an expiry.
3. The first confirmed accept wins: the replacement appointment is written
   back to the calendar, and every other pending offer for the slot is
   stood down with a polite message.
4. Offers that pass their expiry unanswered are marked expired.

Every transition is written to the state store, so the whole history of a
slot can be audited.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .calendars.base import Appointment, CalendarAdapter
from .config import Pack
from .notify.base import Notifier
from .reminders import format_start, render_template
from .store import StateStore
from .waitlist import WaitlistEntry, matching_entries


class BackfillEngine:
    def __init__(self, calendar: CalendarAdapter, entries: list[WaitlistEntry],
                 pack: Pack, notifier: Notifier, store: StateStore,
                 business_name: str = "Your Business",
                 expiry_minutes: int | None = None, max_offers: int | None = None):
        self.calendar = calendar
        self.entries = entries
        self.pack = pack
        self.notifier = notifier
        self.store = store
        self.business_name = business_name
        self.expiry_minutes = (
            pack.offer_expiry_minutes if expiry_minutes is None else expiry_minutes
        )
        self.max_offers = pack.max_offers if max_offers is None else max_offers

    # ---- offers ----------------------------------------------------------
    def handle_cancellation(self, cancelled: Appointment,
                            now: datetime) -> list[dict]:
        """Offer a freed slot to the first matching waitlist entries."""
        matches = matching_entries(
            self.entries, cancelled.service, cancelled.start, cancelled.end
        )[: self.max_offers]
        created: list[dict] = []
        expires_at = now + timedelta(minutes=self.expiry_minutes)
        for entry in matches:
            offer_id = self.store.create_offer(
                appointment_id=cancelled.id,
                slot_service=cancelled.service,
                slot_start=cancelled.start,
                slot_end=cancelled.end,
                waitlist_name=entry.name,
                contact=entry.contact,
                created_at=now,
                expires_at=expires_at,
            )
            body = render_template(
                self.pack.template("offer"),
                name=entry.name,
                service=cancelled.service,
                start=format_start(cancelled.start),
                business=self.business_name,
                expiry_minutes=self.expiry_minutes,
            )
            subject = f"A {cancelled.service} slot just opened: {format_start(cancelled.start)}"
            self.notifier.send(entry.contact, subject, body, kind="offer")
            self.store.log_send("offer", entry.contact, subject, body, now)
            offer = self.store.get_offer(offer_id)
            assert offer is not None
            created.append(offer)
        return created

    # ---- expiry ------------------------------------------------------------
    def expire_offers(self, now: datetime) -> int:
        count = 0
        for offer in self.store.list_offers():
            if offer["status"] == "pending" and datetime.fromisoformat(
                offer["expires_at"]
            ) <= now:
                self.store.set_offer_status(offer["id"], "expired", now)
                count += 1
        return count

    # ---- acceptance ----------------------------------------------------------
    def accept(self, contact: str, now: datetime) -> Appointment | None:
        """Accept the pending offer held by `contact`. First accept wins.

        Returns the written-back appointment, or None if this contact holds
        no live offer (none, expired, or already resolved).
        """
        offer = self.store.pending_offer_for_contact(contact)
        if offer is None:
            return None
        if datetime.fromisoformat(offer["expires_at"]) <= now:
            self.store.set_offer_status(offer["id"], "expired", now)
            return None

        slot_start = datetime.fromisoformat(offer["slot_start"])
        slot_end = datetime.fromisoformat(offer["slot_end"])
        self.store.set_offer_status(offer["id"], "accepted", now)
        new_appt = self.calendar.create_appointment(
            Appointment(
                id="",
                title=f"{offer['slot_service']} (waitlist backfill)",
                service=offer["slot_service"],
                start=slot_start,
                end=slot_end,
                attendee_name=offer["waitlist_name"],
                attendee_contact=offer["contact"],
                status="confirmed",
            )
        )

        booked_body = render_template(
            self.pack.template("booked"),
            name=offer["waitlist_name"],
            service=offer["slot_service"],
            start=format_start(slot_start),
            business=self.business_name,
        )
        booked_subject = f"Booked: {offer['slot_service']} on {format_start(slot_start)}"
        self.notifier.send(contact, booked_subject, booked_body, kind="booked")
        self.store.log_send("booked", contact, booked_subject, booked_body, now)

        # Everyone else with a live offer for this slot is stood down.
        for other in self.store.offers_for_appointment(
            offer["appointment_id"], status="pending"
        ):
            self.store.set_offer_status(other["id"], "stood_down", now)
            body = render_template(
                self.pack.template("stood_down"),
                name=other["waitlist_name"],
                service=offer["slot_service"],
                start=format_start(slot_start),
                business=self.business_name,
            )
            subject = f"Update on the {offer['slot_service']} slot at {format_start(slot_start)}"
            self.notifier.send(other["contact"], subject, body, kind="stood_down")
            self.store.log_send("stood_down", other["contact"], subject, body, now)
        return new_appt

    def decline(self, contact: str, now: datetime) -> bool:
        offer = self.store.pending_offer_for_contact(contact)
        if offer is None:
            return False
        self.store.set_offer_status(offer["id"], "declined", now)
        return True
