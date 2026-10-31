# Contributing to SlotFill

Thanks for considering it. SlotFill is deliberately small and deterministic,
which makes it a friendly project for first-time contributors.

## Dev setup (under 10 minutes)

```bash
git clone https://github.com/techaurah/slotfill.git
cd slotfill
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest          # whole suite runs offline in seconds
slotfill demo             # see the full flow end to end
```

No credentials, accounts or services are needed for any of this: the test
suite and demo run against the fake calendar and the dry-run notifier.

## Great first contributions

- **A vertical pack** (data only): one YAML file in `packs/` for a new
  trade or clinic type. See `docs/packs.md`. Use the "New vertical pack"
  issue template.
- **A message template pack** for a new language: same templates, natural
  wording, same placeholders.
- **The CalDAV adapter**: the contract is written out in
  `src/slotfill/calendars/caldav.py`.
- **Tests** for a documented edge case, or a clearer error message.

## How to claim an issue

Comment on the issue saying you would like to work on it, and wait for a
maintainer to assign it before starting large work. Small fixes (typos,
docs, a single test) need no assignment: just open the PR.

## PR rules

- Link the issue in the PR description (`Closes #123`). PRs without an
  issue are fine for small fixes; say so in the description.
- Include test evidence: the command you ran and its result. "Tested
  locally" is not evidence.
- Keep the invariants: deterministic behaviour only (no LLM calls), first
  confirmed accept wins, every send and offer logged in the store, and the
  demo must stay fully offline.
- Code style: Python 3.11+, type hints on public functions, no new runtime
  dependencies without a discussion in the issue first.
- No em dashes in prose, docs or commit messages.
- First response target: a maintainer replies to PRs and issues within a
  few days, not hours. Honest beats heroic.

## Releases

Semantic Versioning. Changes land in the `Unreleased` section of
`CHANGELOG.md` with every PR that changes behaviour.
