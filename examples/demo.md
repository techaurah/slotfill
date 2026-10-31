# Demo walkthrough

Run it:

```bash
slotfill demo
# or, without installing:
PYTHONPATH=src python -m slotfill.cli demo
```

Fully offline. Nothing is sent: the default notifier is the dry-run log
notifier, and the calendar is the in-memory fake.

## The scenario

BrightSmile Clinic, Monday 09:00. Three appointments are on the books:

- A-100: Maria Lopez, checkup today at 11:00 (her 2h reminder is due).
- A-101: Tom Reed, checkup tomorrow at 10:00.
- A-102: Priya Shah, vaccination on Wednesday at 09:00 (her 48h reminder is due).

The waitlist (`examples/waitlist.csv`) holds four people. Ana, Ben and Cara
all want a checkup and can make tomorrow 10:00. Dan wants a vaccination, so
he must not be offered the checkup slot.

## What the demo shows, step by step

1. Tom Reed cancels A-101.
2. One `run_cycle` fires the two due reminders, notices the cancellation,
   and offers the freed slot to Ana, Ben and Cara in waitlist order, each
   with a 30-minute expiry (the clinic pack's setting).
3. Ben replies "YES please" before Ana does. First confirmed accept wins:
   a replacement appointment for Ben is written back to the calendar, and
   Ana and Cara receive polite stand-down messages.
4. The demo prints the calendar after backfill and the offer ledger from
   the SQLite store: one accepted, two stood down, and a full log of every
   message that would have been sent.

Every behaviour in this walkthrough is covered by the test suite
(`python -m pytest`), including idempotency: running a second cycle at the
same time sends nothing twice.
