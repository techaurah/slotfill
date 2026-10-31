<h1 align="center">SlotFill</h1>

<p align="center"><strong>TechAurah open source</strong></p>

**SlotFill is a no-show recovery service that sends appointment reminders and backfills cancelled slots from your waitlist, on the calendar you already use.**

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-offline%20pytest-brightgreen.svg)

[Docs](docs/setup.md) · [Examples](examples/demo.md) · [Vertical packs](docs/packs.md) · [Notifiers](docs/notifiers.md) · [TechAurah](https://techaurah.com)

## The problem

Appointment businesses lose a slot twice when a client no-shows or cancels late: the hour sits empty, and the waitlisted client who would happily have taken it is never asked. Clinic no-show rates run at 12 to 42% across settings (systematic review, Mazaheri Habibi et al., 2024), and MGMA DataDive 2025 found 19.95% of appointments were cancelled in 2024 while only 27.4% of those were rescheduled within 30 days. The empty slot is mostly a cancellation problem, which is why reminders alone are not the fix.

The market's answers are to rip out your booking system for a platform, or to pay per-staff SaaS. SlotFill does neither.

**SlotFill does** reminders, waitlist backfill and a full audit log on top of your existing calendar. **It does not** take bookings, replace your booking system, or talk to your clients with an AI. There is no LLM anywhere in v0.1: every behaviour is deterministic, testable state-machine logic.

## Demo

`slotfill demo` runs the whole flow offline on a fake calendar. Nothing is sent. Abridged output:

```
Step 1: Tom Reed cancels tomorrow's 10:00 checkup (A-101).
Step 2: Run one SlotFill cycle (reminders + backfill offers).
  Cycle summary: {'reminders_sent': 2, 'offers_expired': 0, 'cancellations': 1, 'offers_created': 3}
Step 3: Ben Cole (2nd on the waitlist) replies YES first.
  Reply action: backfill_accepted:fake-1
Step 5: Offer ledger in the state store:
  offer #1  Ana Ruiz    slot 2026-11-03T10:00:00  status: stood_down
  offer #2  Ben Cole    slot 2026-11-03T10:00:00  status: accepted
  offer #3  Cara Diaz   slot 2026-11-03T10:00:00  status: stood_down
```

Full annotated walkthrough: [examples/demo.md](examples/demo.md).

## Quickstart (5 minutes, zero accounts)

```bash
git clone https://github.com/techaurah/slotfill.git
cd slotfill
python -m pip install -e .
slotfill demo
python -m pytest   # the whole suite, offline
```

Prerequisites: Python 3.11 or newer. That is all. The demo and tests use the bundled fake calendar, the example waitlist and the dry-run notifier, so a stranger can see SlotFill work before configuring anything. Real setup (SMTP, Google Calendar status, scheduling cycles) is in [docs/setup.md](docs/setup.md).

## What it does

- [x] **Reminder sequences per vertical** driven by data packs: offsets, templates and reply keywords for [clinic](packs/clinic.yaml), [salon](packs/salon.yaml) and [home services](packs/home-services.yaml)
- [x] **Confirm and reschedule reply handling** by keyword, with acknowledgements
- [x] **Waitlist in a plain CSV** any business can export or type, matched in order by service and acceptable time window ([format](docs/packs.md))
- [x] **Backfill state machine**: cancellation, offer with expiry, first confirmed accept wins, write-back to the calendar, everyone else stood down politely
- [x] **Calendar adapters behind one interface**: a fully working fake calendar, a Google Calendar adapter that validates configuration and fails clearly when unconfigured, and a CalDAV stub with a written contract ([status, honestly](docs/setup.md))
- [x] **Pluggable notifiers**: SMTP email, plus a dry-run log notifier as the default so a fresh install sends nothing ([contracts](docs/notifiers.md))
- [x] **SQLite state store** logging every send and every offer: no reminder is ever sent twice, and every backfill decision can be audited
- [x] **Idempotent cycles**: run it on any schedule; re-running a cycle at the same time is a no-op

## Configuration

The settings people actually touch (full reference in [docs/setup.md](docs/setup.md) and `.env.example`):

| Setting | Env variable | Default |
|---|---|---|
| Vertical pack | `SLOTFILL_PACK` | `packs/clinic.yaml` |
| Waitlist CSV | `SLOTFILL_WAITLIST` | `examples/waitlist.csv` |
| State store | `SLOTFILL_DB` | `slotfill.db` |
| Business name in messages | `SLOTFILL_BUSINESS_NAME` | `Your Business` |
| Email sending | `SLOTFILL_SMTP_HOST` and friends | unset, so dry-run |
| Google Calendar credentials | `SLOTFILL_GOOGLE_CREDENTIALS` | unset |

## Examples

| Example | What it shows | Time | Credentials |
|---|---|---|---|
| `slotfill demo` ([walkthrough](examples/demo.md)) | Full cycle: reminders, cancellation, offers, accept, write-back, stand-downs | 1 minute | None |
| [Example waitlist](examples/waitlist.csv) | The CSV format, including a non-matching entry that is correctly never offered a slot | 1 minute | None |
| Test suite (`tests/`) | Every state machine transition, executable | 2 minutes | None |

## Roadmap

- **Now:** v0.1, this release. Fake calendar demo, email notifier, three vertical packs.
- **Next:** live Google Calendar API wiring (contract written in [docs/setup.md](docs/setup.md)); CalDAV adapter implementation.
- **Later:** WhatsApp and SMS notifier adapters, each with its own compliance review before it can send (see [docs/notifiers.md](docs/notifiers.md)); Sheet-backed waitlist as an alternative to CSV. A full conversational booking agent is a recorded possible evolution, not a promise.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), find a `good first issue`, and open a PR that links its issue and passes CI. The easiest first contribution is a vertical pack: one YAML data file, no code. Calendar adapters and template packs are also well-bounded. Response rhythm and PR rules are in CONTRIBUTING.

## Community and support

| Channel | Best for |
|---|---|
| [Issues](https://github.com/techaurah/slotfill/issues) | Bugs and concrete feature work |
| [Discussions](https://github.com/techaurah/slotfill/discussions) | Questions, ideas, show and tell |
| [SECURITY.md](SECURITY.md) | Vulnerabilities (private, never a public issue) |
| [TechAurah website](https://techaurah.com) | The company behind the project |

## License

MIT. See [LICENSE](LICENSE).

## About TechAurah

TechAurah is an AI and software engineering company building products, agents and automation for service businesses, and publishing the deterministic parts as open source. We are available for AI engineering projects: https://techaurah.com
