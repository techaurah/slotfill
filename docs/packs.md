# Vertical packs and the waitlist format

## Vertical packs

A pack is a single YAML data file in `packs/`. It carries everything that
differs between a clinic, a salon and a plumber, so the engine code never
changes per vertical:

```yaml
name: clinic                 # unique pack name
vertical: clinic             # display category
offer_expiry_minutes: 30     # how long an offer stays live
max_offers: 3                # how many waitlist entries are offered at once
reminders:                   # reminder sequence before an appointment
  - offset: 48h              # offsets accept 30m, 2h, 1d forms
    template: reminder       # which template to send
templates:
  reminder: "Hi {name}, ..."        # placeholders: name, service, start,
  offer: "Hi {name}, ..."           # business, expiry_minutes, offset
  stood_down: "Hi {name}, ..."
  booked: "Hi {name}, ..."
  confirm_ack: "Hi {name}, ..."
  reschedule_ack: "Thanks, ..."
keywords:
  confirm: ["yes", "confirm", "ok"]
  reschedule: ["reschedule", "move", "change"]
```

Rules that keep packs safe:

- All six templates are required; the loader fails loudly if one is missing
  at send time.
- Keep reminder wording short and reply-friendly: every template should tell
  the client exactly which keyword to reply with.
- Reply classification checks reschedule keywords before confirm keywords,
  so "change it, yes" is a move request, not a confirmation.

### Contributing a pack

Packs are the easiest first contribution in this project: no code. Open an
issue with the "New vertical pack" template, then a PR adding one YAML file
plus a line in the table in the README. Good candidates: dental, physio,
driving instructors, tattoo studios, pet grooming, tutoring.

## The waitlist CSV

`examples/waitlist.csv` is the reference format:

```csv
name,contact,service,earliest,latest
Ana Ruiz,ana@example.com,checkup,2026-11-03 08:00,2026-11-03 12:00
```

- `name`, `contact`: who to offer the slot to, and where (email in v0.1).
- `service`: must match the calendar service name (case-insensitive).
  Leave blank to accept any service.
- `earliest`, `latest`: the acceptable window. A freed slot matches only if
  it starts at or after `earliest` and ends at or before `latest`. Either
  may be left blank for "no limit".
- Row order is priority order: first come, first offered. SlotFill never
  reorders your waitlist.
