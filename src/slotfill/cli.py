"""SlotFill command line.

Commands:
  slotfill demo       Run the full offline demo cycle on the fake calendar.
  slotfill run-cycle  Run one reminder/backfill cycle on the fake calendar
                      with the demo seed data (nothing is really sent).
  slotfill offers     List offers recorded in the state store.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from .calendars.base import Appointment
from .calendars.fake import FakeCalendar
from .config import Settings, load_pack
from .notify.base import LogNotifier
from .scheduler import SlotfillService
from .store import StateStore
from .waitlist import load_waitlist

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_NOW = datetime(2026, 11, 2, 9, 0)  # a Monday, 09:00
BUSINESS = "BrightSmile Clinic"


def seed_calendar() -> FakeCalendar:
    return FakeCalendar(
        [
            Appointment(
                id="A-100",
                title="Checkup: Maria Lopez",
                service="checkup",
                start=DEMO_NOW + timedelta(hours=2),
                end=DEMO_NOW + timedelta(hours=2, minutes=30),
                attendee_name="Maria Lopez",
                attendee_contact="maria@example.com",
            ),
            Appointment(
                id="A-101",
                title="Checkup: Tom Reed",
                service="checkup",
                start=datetime(2026, 11, 3, 10, 0),
                end=datetime(2026, 11, 3, 10, 30),
                attendee_name="Tom Reed",
                attendee_contact="tom@example.com",
            ),
            Appointment(
                id="A-102",
                title="Vaccination: Priya Shah",
                service="vaccination",
                start=datetime(2026, 11, 4, 9, 0),
                end=datetime(2026, 11, 4, 9, 15),
                attendee_name="Priya Shah",
                attendee_contact="priya@example.com",
            ),
        ]
    )


def build_demo_service(store: StateStore) -> tuple[SlotfillService, FakeCalendar]:
    pack = load_pack(REPO_ROOT / "packs" / "clinic.yaml")
    entries = load_waitlist(REPO_ROOT / "examples" / "waitlist.csv")
    calendar = seed_calendar()
    notifier = LogNotifier()
    service = SlotfillService(calendar, entries, pack, notifier, store, BUSINESS)
    return service, calendar


def cmd_demo(_args: argparse.Namespace) -> int:
    store = StateStore(":memory:")
    service, calendar = build_demo_service(store)
    now = DEMO_NOW
    print("=" * 68)
    print("SlotFill demo: one clinic morning, fully offline, nothing sent")
    print(f"Business: {BUSINESS}   Now: {now:%a %d %b %Y %H:%M}")
    print("=" * 68)

    print("\nStep 1: Tom Reed cancels tomorrow's 10:00 checkup (A-101).")
    calendar.cancel_appointment("A-101")

    print("\nStep 2: Run one SlotFill cycle (reminders + backfill offers).")
    summary = service.run_cycle(now)
    print(f"  Cycle summary: {summary}")

    print("\nStep 3: Ben Cole (2nd on the waitlist) replies YES first.")
    result = service.handle_reply("ben@example.com", "YES please", now)
    print(f"  Reply action: {result}")

    print("\nStep 4: Calendar after backfill (note the new appointment):")
    for appt in calendar.list_appointments(now, now + timedelta(days=7)):
        print(
            f"  {appt.id:>7}  {appt.start:%a %d %b %H:%M}  {appt.service:<12}"
            f" {appt.attendee_name} [{appt.status}]"
        )

    print("\nStep 5: Offer ledger in the state store:")
    for offer in store.list_offers():
        print(
            f"  offer #{offer['id']}  {offer['waitlist_name']:<10}"
            f" slot {offer['slot_start']}  status: {offer['status']}"
        )
    print(f"\nTotal messages logged in the store: {store.count_sends()}")
    print("Demo complete: the freed slot was refilled, nobody was messaged twice,")
    print("and every step above is reproducible by the test suite (python -m pytest).")
    return 0


def cmd_run_cycle(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    store = StateStore(settings.db_path)
    service, _calendar = build_demo_service(store)
    now = datetime.fromisoformat(args.now) if args.now else DEMO_NOW
    summary = service.run_cycle(now)
    print(summary)
    return 0


def cmd_offers(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    store = StateStore(args.db or settings.db_path)
    offers = store.list_offers()
    if not offers:
        print("No offers recorded.")
        return 0
    for offer in offers:
        print(
            f"#{offer['id']}  {offer['waitlist_name']} ({offer['contact']})"
            f"  {offer['slot_service']} at {offer['slot_start']}"
            f"  status: {offer['status']}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slotfill", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Run the full offline demo cycle")
    run = sub.add_parser("run-cycle", help="Run one cycle on the demo seed data")
    run.add_argument("--now", default=None, help="ISO datetime to run as 'now'")
    offers = sub.add_parser("offers", help="List offers in the state store")
    offers.add_argument("--db", default=None, help="Path to the SQLite store")

    args = parser.parse_args(argv)
    if args.command == "demo":
        return cmd_demo(args)
    if args.command == "run-cycle":
        return cmd_run_cycle(args)
    if args.command == "offers":
        return cmd_offers(args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
