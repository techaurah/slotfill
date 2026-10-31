from datetime import datetime, timedelta
from pathlib import Path

from slotfill.calendars.base import Appointment
from slotfill.calendars.fake import FakeCalendar
from slotfill.calendars.google import GoogleCalendarAdapter
from slotfill.calendars.base import CalendarNotConfiguredError
from slotfill.config import load_pack
from slotfill.notify.base import LogNotifier
from slotfill.scheduler import SlotfillService
from slotfill.store import StateStore
from slotfill.waitlist import load_waitlist

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 2, 9, 0)


def make_service(tmp_path):
    pack = load_pack(REPO_ROOT / "packs" / "clinic.yaml")
    entries = load_waitlist(REPO_ROOT / "examples" / "waitlist.csv")
    calendar = FakeCalendar(
        [
            Appointment(
                id="A-100", title="Checkup: Maria Lopez", service="checkup",
                start=NOW + timedelta(hours=2), end=NOW + timedelta(hours=2, minutes=30),
                attendee_name="Maria Lopez", attendee_contact="maria@example.com",
            ),
            Appointment(
                id="A-101", title="Checkup: Tom Reed", service="checkup",
                start=datetime(2026, 11, 3, 10, 0), end=datetime(2026, 11, 3, 10, 30),
                attendee_name="Tom Reed", attendee_contact="tom@example.com",
            ),
        ]
    )
    store = StateStore(tmp_path / "state.db")
    service = SlotfillService(calendar, entries, pack, LogNotifier(echo=False),
                              store, "BrightSmile Clinic")
    return service, calendar, store


def test_full_cycle_cancel_offer_accept(tmp_path):
    service, calendar, store = make_service(tmp_path)
    calendar.cancel_appointment("A-101")
    summary = service.run_cycle(NOW)
    assert summary["cancellations"] == 1
    assert summary["offers_created"] == 3
    assert summary["reminders_sent"] == 1  # Maria's 2h reminder

    result = service.handle_reply("ben@example.com", "YES", NOW + timedelta(minutes=3))
    assert result.startswith("backfill_accepted:")
    upcoming = calendar.list_appointments(NOW, NOW + timedelta(days=7))
    assert any(a.attendee_name == "Ben Cole" for a in upcoming)


def test_second_cycle_is_idempotent(tmp_path):
    service, calendar, _store = make_service(tmp_path)
    calendar.cancel_appointment("A-101")
    first = service.run_cycle(NOW)
    second = service.run_cycle(NOW)
    assert first["reminders_sent"] == 1
    assert second == {
        "reminders_sent": 0,
        "offers_expired": 0,
        "cancellations": 0,
        "offers_created": 0,
    }


def test_reply_confirm_marks_appointment(tmp_path):
    service, _calendar, store = make_service(tmp_path)
    service.run_cycle(NOW)
    result = service.handle_reply("maria@example.com", "yes", NOW)
    assert result == "appointment_confirmed:A-100"
    assert store.is_confirmed("A-100")


def test_reply_reschedule_from_offer_holder_declines_offer(tmp_path):
    service, calendar, store = make_service(tmp_path)
    calendar.cancel_appointment("A-101")
    service.run_cycle(NOW)
    result = service.handle_reply("ana@example.com", "I need to reschedule", NOW)
    assert result == "reschedule_requested"
    statuses = {o["waitlist_name"]: o["status"] for o in store.list_offers()}
    assert statuses["Ana Ruiz"] == "declined"


def test_google_adapter_without_credentials_fails_clearly(monkeypatch):
    monkeypatch.delenv("SLOTFILL_GOOGLE_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    adapter = GoogleCalendarAdapter()
    with pytest.raises(CalendarNotConfiguredError, match="not configured"):
        adapter.list_appointments(NOW, NOW + timedelta(days=1))
