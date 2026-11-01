# Roadmap: SlotFill

Where SlotFill is going after v0.1.0. This is a plan, not a
promise: items land when they are built, tested, and reviewed, in
roughly this order.

## What v0.2 adds

- **Google Calendar live wiring:** the adapter contract is
  already written and validated in docs/setup.md; v0.2 wires
  the real Calendar API calls behind it, tested against a live
  calendar.
- **CalDAV adapter:** an implementation behind the existing
  contract, for calendars that are not Google.
- **WhatsApp and SMS notifiers:** sender adapters behind the
  existing notifier interface, each with its own compliance
  review before it can send.
- Sheet-backed waitlist as an alternative to the CSV waitlist.

## Deliberately out of scope

- **Not a booking system.** SlotFill never takes bookings and
  never replaces the booking system you already use; it works
  on the calendar that system maintains.
- **No LLM and no conversational AI.** Every behaviour stays
  deterministic state-machine logic that can be tested exactly.
- **No unsolicited messaging.** Reminders and offers go only to
  people already on your books or your waitlist.

## How priorities are set

Priorities are set from GitHub issues and Discussions: open an
issue for concrete, actionable work, and start a discussion for
ideas and questions. Adapter work is prioritised by which
calendars and channels users actually run.
