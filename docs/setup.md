# Setup

## The 5-minute path (offline demo)

No accounts, no credentials, nothing is sent:

```bash
git clone <this repo> && cd slotfill
python -m pip install -e .
slotfill demo
```

Or without installing:

```bash
PYTHONPATH=src python -m slotfill.cli demo
```

The demo seeds a fake calendar for a small clinic, cancels an appointment,
and runs the whole cycle: reminders, waitlist offers, one accept, write-back
to the calendar, and stand-down messages for everyone else. See
`examples/demo.md` for the annotated walkthrough.

## Running it for real

1. Copy `.env.example` to `.env` and set:
   - `SLOTFILL_BUSINESS_NAME`: the name clients see in messages.
   - `SLOTFILL_PACK`: which vertical pack to use (`packs/clinic.yaml`,
     `packs/salon.yaml`, `packs/home-services.yaml`, or your own).
   - `SLOTFILL_WAITLIST`: path to your waitlist CSV (format in
     `docs/packs.md` and `examples/waitlist.csv`).
   - `SLOTFILL_DB`: where the SQLite state store lives.
2. Choose a notifier. The default is the dry-run log notifier, which prints
   what would be sent and delivers nothing. To send real email, set the
   `SLOTFILL_SMTP_*` variables (see `.env.example`).
3. Choose a calendar adapter (below) and run cycles on a schedule (cron,
   a systemd timer, or your own loop calling
   `SlotfillService.run_cycle(now)`).

## Calendar adapters in v0.1, honestly

| Adapter | Status in v0.1 |
|---|---|
| Fake calendar | Fully working. Used by the demo and the entire test suite. |
| Google Calendar | Configuration validation only. Constructing it without credentials raises a clear `CalendarNotConfiguredError` telling you exactly what to set. With credentials present, live API calls raise `NotImplementedError` pointing at the wiring contract below. Nothing is silently faked. |
| CalDAV | Documented stub. Every method raises `NotImplementedError` with the implementation contract (also in `src/slotfill/calendars/caldav.py`). A well-scoped contribution. |

### Google Calendar wiring contract (next step)

To finish the Google adapter, implement the three interface methods in
`src/slotfill/calendars/google.py` using the Calendar API v3:

- `list_appointments(start, end)`: `events.list` with `timeMin`/`timeMax`,
  `singleEvents=True`, skipping events with `status == "cancelled"`; map
  summary, start/end dateTime, and the attendee email.
- `create_appointment(appointment)`: `events.insert` with the stored slot
  and attendee; return the appointment with the created event id.
- `get_cancellations()`: poll with a stored `syncToken` (or watch channel)
  and report events whose status changed to `cancelled`, exactly once each.

Credentials: a service account key shared with the target calendar, or
OAuth user credentials. Set `SLOTFILL_GOOGLE_CREDENTIALS` to the JSON path
and `SLOTFILL_GOOGLE_CALENDAR_ID` to the calendar id.

### How service names are matched

Waitlist matching compares the appointment's `service` string with the
waitlist entry's `service` (case-insensitive). Keep service names consistent
between your calendar events and the waitlist CSV: one canonical name per
service ("checkup", "haircut", "boiler service").
