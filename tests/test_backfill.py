from datetime import datetime, timedelta
from pathlib import Path

from slotfill.backfill import BackfillEngine
from slotfill.calendars.base import Appointment
from slotfill.calendars.fake import FakeCalendar
from slotfill.config import load_pack
from slotfill.notify.base import LogNotifier
from slotfill.store import StateStore
from slotfill.waitlist import load_waitlist

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 2, 9, 0)
SLOT_START = datetime(2026, 11, 3, 10, 0)
SLOT_END = datetime(2026, 11, 3, 10, 30)


def make_engine(tmp_path):
    pack = load_pack(REPO_ROOT / "packs" / "clinic.yaml")
    entries = load_waitlist(REPO_ROOT / "examples" / "waitlist.csv")
    cancelled = Appointment(
        id="A-101", title="Checkup: Tom Reed", service="checkup",
        start=SLOT_START, end=SLOT_END, attendee_name="Tom Reed",
        attendee_contact="tom@example.com", status="cancelled",
    )
    calendar = FakeCalendar([cancelled])
    notifier = LogNotifier(echo=False)
    store = StateStore(tmp_path / "state.db")
    engine = BackfillEngine(calendar, entries, pack, notifier, store, "BrightSmile Clinic")
    return engine, calendar, notifier, store, cancelled


def test_cancellation_offers_first_matches_in_order(tmp_path):
    engine, _cal, notifier, store, cancelled = make_engine(tmp_path)
    offers = engine.handle_cancellation(cancelled, NOW)
    assert [o["waitlist_name"] for o in offers] == ["Ana Ruiz", "Ben Cole", "Cara Diaz"]
    assert all(o["status"] == "pending" for o in offers)
    assert store.count_sends("offer") == 3
    assert len(notifier.sent) == 3


def test_first_confirmed_accept_wins_and_writes_back(tmp_path):
    engine, calendar, _notifier, store, cancelled = make_engine(tmp_path)
    engine.handle_cancellation(cancelled, NOW)

    # Ben (second in line) confirms first: he gets the slot.
    new_appt = engine.accept("ben@example.com", NOW + timedelta(minutes=5))
    assert new_appt is not None
    assert new_appt.attendee_name == "Ben Cole"
    assert new_appt.start == SLOT_START

    statuses = {o["waitlist_name"]: o["status"] for o in store.list_offers()}
    assert statuses == {
        "Ana Ruiz": "stood_down",
        "Ben Cole": "accepted",
        "Cara Diaz": "stood_down",
    }
    # The replacement is on the calendar; a later accept attempt wins nothing.
    upcoming = calendar.list_appointments(NOW, NOW + timedelta(days=7))
    assert any(a.attendee_contact == "ben@example.com" for a in upcoming)
    assert engine.accept("ana@example.com", NOW + timedelta(minutes=6)) is None
    assert store.count_sends("stood_down") == 2
    assert store.count_sends("booked") == 1


def test_offers_expire(tmp_path):
    engine, _cal, _notifier, store, cancelled = make_engine(tmp_path)
    engine.handle_cancellation(cancelled, NOW)
    later = NOW + timedelta(minutes=31)  # clinic pack expiry is 30 minutes
    assert engine.expire_offers(later) == 3
    assert all(o["status"] == "expired" for o in store.list_offers())
    # An expired offer can no longer be accepted.
    assert engine.accept("ana@example.com", later) is None


def test_accept_with_no_offer_returns_none(tmp_path):
    engine, _cal, _n, _s, _c = make_engine(tmp_path)
    assert engine.accept("nobody@example.com", NOW) is None


def test_decline_marks_offer(tmp_path):
    engine, _cal, _n, store, cancelled = make_engine(tmp_path)
    engine.handle_cancellation(cancelled, NOW)
    assert engine.decline("ana@example.com", NOW) is True
    statuses = {o["waitlist_name"]: o["status"] for o in store.list_offers()}
    assert statuses["Ana Ruiz"] == "declined"
    assert statuses["Ben Cole"] == "pending"
