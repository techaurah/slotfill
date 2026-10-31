# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-31

### Added

- Deterministic reminder engine driven by vertical packs (clinic, salon,
  home-services): configurable offsets, message templates, and confirm /
  reschedule reply keywords. No LLM anywhere in the pipeline.
- Waitlist backfill state machine: on a cancellation, the freed slot is
  matched against a CSV waitlist in order, offered with an expiry, and the
  first confirmed accept wins and is written back to the calendar. Everyone
  else is stood down politely.
- Calendar adapters behind one interface: a fully working in-memory fake
  calendar for demos and tests, a Google Calendar adapter that validates
  configuration and fails with a clear not-configured error, and a CalDAV
  adapter stub with a documented contract.
- Pluggable notifier interface with an SMTP email notifier and a dry-run log
  notifier (the default, so the demo sends nothing).
- SQLite state store logging every send and every offer, so nothing is ever
  sent twice and every backfill decision can be audited.
- CLI with an offline end-to-end demo: `slotfill demo`.
