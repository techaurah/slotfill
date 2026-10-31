# AGENTS.md

Instructions for AI coding agents (and humans skimming) working in this repo.

## What this project is

SlotFill is a deterministic no-show recovery service for appointment
businesses: reminders plus waitlist backfill on top of calendars businesses
already use. It is not a booking system and contains no LLM calls. Every
behaviour is testable state-machine logic.

## Layout

- `src/slotfill/` application package
  - `calendars/` calendar adapters behind `base.CalendarAdapter`
    (`fake.py` is fully working; `google.py` validates configuration;
    `caldav.py` is a documented stub)
  - `notify/` notifier interface (`base.py`) and SMTP email (`email.py`);
    the log notifier in `base.py` is the default and sends nothing
  - `reminders.py` reminder engine + reply keyword classification
  - `backfill.py` waitlist backfill state machine
  - `scheduler.py` service that runs one full cycle
  - `store.py` SQLite log of every send and offer
  - `waitlist.py` CSV waitlist loading and matching
  - `config.py` settings and vertical pack loading
  - `cli.py` command line entry points (`slotfill demo`, `run-cycle`, `offers`)
- `packs/` vertical packs as data files (offsets, templates, keywords)
- `examples/` demo waitlist CSV and demo walkthrough
- `tests/` pytest suite, fully offline against the fake calendar

## Commands

- Run tests: `python -m pytest` (uses the `pythonpath` setting in
  `pyproject.toml`; no install needed)
- Run the demo: `PYTHONPATH=src python -m slotfill.cli demo`
  (or `pip install -e .` then `slotfill demo`)

## Conventions

- Python 3.11+, standard library plus PyYAML only. Do not add dependencies
  without a strong reason.
- No em dashes in prose, docs, or commit messages.
- Never make the fake calendar or the log notifier send anything real.
- New behaviour ships with tests against the fake calendar. State machine
  changes must keep the invariant: first confirmed accept wins, everyone
  else is stood down, and every send and offer is written to the store.
- Scale claims in docs must carry a named source and year. Do not add
  unsourced statistics.
