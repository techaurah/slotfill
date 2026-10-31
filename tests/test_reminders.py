from datetime import datetime, timedelta
from pathlib import Path

import pytest

from slotfill.calendars.base import Appointment
from slotfill.config import SlotfillError, load_pack
from slotfill.notify.base import LogNotifier
from slotfill.reminders import ReminderEngine, classify_reply, parse_offset
from slotfill.store import StateStore

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 2, 9, 0)


def make_engine(tmp_path):
    pack = load_pack(REPO_ROOT / "packs" / "clinic.yaml")
    notifier = LogNotifier(echo=False)
    store = StateStore(tmp_path / "state.db")
    return ReminderEngine(pack, notifier, store, "BrightSmile Clinic"), notifier, store


def appt(start, appt_id="A-1", contact="maria@example.com"):
    return Appointment(
        id=appt_id,
        title="Checkup",
        service="checkup",
        start=start,
        end=start + timedelta(minutes=30),
        attendee_name="Maria Lopez",
        attendee_contact=contact,
    )


def test_parse_offset_forms():
    assert parse_offset("30m") == timedelta(minutes=30)
    assert parse_offset("2h") == timedelta(hours=2)
    assert parse_offset("48h") == timedelta(hours=48)
    assert parse_offset("1d") == timedelta(days=1)
    with pytest.raises(SlotfillError):
        parse_offset("soon")


def test_all_packs_load():
    for name in ("clinic", "salon", "home-services"):
        pack = load_pack(REPO_ROOT / "packs" / f"{name}.yaml")
        assert pack.reminders
        for key in ("reminder", "offer", "stood_down", "booked",
                    "confirm_ack", "reschedule_ack"):
            assert key in pack.templates


def test_reminder_due_at_2h_offset(tmp_path):
    engine, notifier, _store = make_engine(tmp_path)
    sent = engine.run([appt(NOW + timedelta(hours=2))], NOW)
    assert len(sent) == 1
    assert sent[0].recipient == "maria@example.com"
    assert "Maria Lopez" in sent[0].body


def test_reminder_not_sent_twice(tmp_path):
    engine, _notifier, _store = make_engine(tmp_path)
    a = appt(NOW + timedelta(hours=2))
    assert len(engine.run([a], NOW)) == 1
    assert engine.run([a], NOW) == []


def test_reminder_not_due_yet_or_after_start(tmp_path):
    engine, _n, _s = make_engine(tmp_path)
    # 26h away: the 24h reminder is not due yet at NOW, 48h fired earlier window only
    assert engine.run([appt(NOW + timedelta(hours=30))], NOW) == []
    # already started: no reminders
    assert engine.run([appt(NOW - timedelta(minutes=5), appt_id="A-2")], NOW) == []


def test_cancelled_appointment_gets_no_reminder(tmp_path):
    engine, _n, _s = make_engine(tmp_path)
    a = appt(NOW + timedelta(hours=2))
    a.status = "cancelled"
    assert engine.run([a], NOW) == []


def test_classify_reply():
    pack = load_pack(REPO_ROOT / "packs" / "clinic.yaml")
    assert classify_reply("YES please", pack) == "confirm"
    assert classify_reply("Confirmed, thanks", pack) == "confirm"
    assert classify_reply("Can I reschedule?", pack) == "reschedule"
    assert classify_reply("I need to change it, yes", pack) == "reschedule"
    assert classify_reply("What are your opening hours?", pack) is None
