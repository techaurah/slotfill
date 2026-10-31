from datetime import datetime
from pathlib import Path

import pytest

from slotfill.config import SlotfillError
from slotfill.waitlist import WaitlistEntry, load_waitlist, matching_entries

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_examples_csv():
    entries = load_waitlist(REPO_ROOT / "examples" / "waitlist.csv")
    assert [e.name for e in entries] == ["Ana Ruiz", "Ben Cole", "Cara Diaz", "Dan Fox"]
    assert entries[0].position == 0
    assert entries[0].earliest == datetime(2026, 11, 3, 8, 0)


def test_matching_respects_service_and_window_in_order():
    entries = load_waitlist(REPO_ROOT / "examples" / "waitlist.csv")
    slot_start = datetime(2026, 11, 3, 10, 0)
    slot_end = datetime(2026, 11, 3, 10, 30)
    matched = matching_entries(entries, "checkup", slot_start, slot_end)
    # Dan Fox wants vaccination, so he is not matched to a checkup slot.
    assert [e.name for e in matched] == ["Ana Ruiz", "Ben Cole", "Cara Diaz"]


def test_entry_outside_window_does_not_match():
    entry = WaitlistEntry(
        name="Early Bird",
        contact="early@example.com",
        service="checkup",
        earliest=datetime(2026, 11, 3, 8, 0),
        latest=datetime(2026, 11, 3, 9, 0),
    )
    assert not entry.matches(
        "checkup", datetime(2026, 11, 3, 10, 0), datetime(2026, 11, 3, 10, 30)
    )


def test_service_match_is_case_insensitive_and_blank_matches_any():
    any_service = WaitlistEntry(name="Any", contact="a@example.com", service="")
    assert any_service.matches(
        "CHECKUP", datetime(2026, 11, 3, 10, 0), datetime(2026, 11, 3, 10, 30)
    )


def test_missing_columns_raise(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("name,contact\nAna,ana@example.com\n", encoding="utf-8")
    with pytest.raises(SlotfillError):
        load_waitlist(bad)
