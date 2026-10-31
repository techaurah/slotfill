"""SQLite state store: every send and every offer is logged.

The store is what makes SlotFill safe to run on a schedule: a reminder is
never sent twice, an offer's full history can be audited, and the backfill
state machine can be reconstructed after a crash.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id TEXT NOT NULL,
    slot_service TEXT NOT NULL,
    slot_start TEXT NOT NULL,
    slot_end TEXT NOT NULL,
    waitlist_name TEXT NOT NULL,
    contact TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    resolved_at TEXT
);
CREATE TABLE IF NOT EXISTS reminders_sent (
    appointment_id TEXT NOT NULL,
    offset TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    PRIMARY KEY (appointment_id, offset)
);
CREATE TABLE IF NOT EXISTS appointment_state (
    appointment_id TEXT PRIMARY KEY,
    confirmed INTEGER NOT NULL DEFAULT 0
);
"""

# Offer statuses: pending, accepted, stood_down, expired, declined


class StateStore:
    def __init__(self, path: str | Path = "slotfill.db"):
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ---- sends ---------------------------------------------------------
    def log_send(self, kind: str, recipient: str, subject: str, body: str,
                 ts: datetime) -> int:
        cur = self._conn.execute(
            "INSERT INTO sends (ts, kind, recipient, subject, body)"
            " VALUES (?, ?, ?, ?, ?)",
            (ts.isoformat(), kind, recipient, subject, body),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def count_sends(self, kind: str | None = None) -> int:
        if kind is None:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM sends").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM sends WHERE kind = ?", (kind,)
            ).fetchone()
        return int(row["n"])

    def list_sends(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM sends ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    # ---- reminders -------------------------------------------------------
    def was_reminder_sent(self, appointment_id: str, offset: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM reminders_sent WHERE appointment_id = ? AND offset = ?",
            (appointment_id, offset),
        ).fetchone()
        return row is not None

    def mark_reminder_sent(self, appointment_id: str, offset: str,
                           ts: datetime) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO reminders_sent (appointment_id, offset, sent_at)"
            " VALUES (?, ?, ?)",
            (appointment_id, offset, ts.isoformat()),
        )
        self._conn.commit()

    # ---- appointment confirmations ---------------------------------------
    def mark_confirmed(self, appointment_id: str) -> None:
        self._conn.execute(
            "INSERT INTO appointment_state (appointment_id, confirmed) VALUES (?, 1)"
            " ON CONFLICT(appointment_id) DO UPDATE SET confirmed = 1",
            (appointment_id,),
        )
        self._conn.commit()

    def is_confirmed(self, appointment_id: str) -> bool:
        row = self._conn.execute(
            "SELECT confirmed FROM appointment_state WHERE appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        return bool(row and row["confirmed"])

    # ---- offers ------------------------------------------------------------
    def create_offer(self, appointment_id: str, slot_service: str,
                     slot_start: datetime, slot_end: datetime,
                     waitlist_name: str, contact: str,
                     created_at: datetime, expires_at: datetime) -> int:
        cur = self._conn.execute(
            "INSERT INTO offers (appointment_id, slot_service, slot_start,"
            " slot_end, waitlist_name, contact, status, created_at, expires_at)"
            " VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
            (
                appointment_id,
                slot_service,
                slot_start.isoformat(),
                slot_end.isoformat(),
                waitlist_name,
                contact,
                created_at.isoformat(),
                expires_at.isoformat(),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def get_offer(self, offer_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM offers WHERE id = ?", (offer_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_offers(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM offers ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def offers_for_appointment(self, appointment_id: str,
                               status: str | None = None) -> list[dict]:
        if status is None:
            rows = self._conn.execute(
                "SELECT * FROM offers WHERE appointment_id = ? ORDER BY id",
                (appointment_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM offers WHERE appointment_id = ? AND status = ?"
                " ORDER BY id",
                (appointment_id, status),
            ).fetchall()
        return [dict(r) for r in rows]

    def pending_offer_for_contact(self, contact: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM offers WHERE contact = ? AND status = 'pending'"
            " ORDER BY id LIMIT 1",
            (contact,),
        ).fetchone()
        return dict(row) if row else None

    def set_offer_status(self, offer_id: int, status: str,
                         resolved_at: datetime) -> None:
        self._conn.execute(
            "UPDATE offers SET status = ?, resolved_at = ? WHERE id = ?",
            (status, resolved_at.isoformat(), offer_id),
        )
        self._conn.commit()
