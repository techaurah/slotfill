"""Settings and vertical pack loading for SlotFill."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class SlotfillError(RuntimeError):
    """Base error for SlotFill configuration and runtime problems."""


@dataclass
class ReminderRule:
    offset: str
    template: str = "reminder"


@dataclass
class Pack:
    """A vertical pack: reminder offsets, templates and reply keywords.

    Packs are data files (see packs/ and docs/packs.md) so a clinic manager
    or salon owner can contribute one without writing code.
    """

    name: str
    vertical: str
    offer_expiry_minutes: int = 30
    max_offers: int = 3
    reminders: list[ReminderRule] = field(default_factory=list)
    templates: dict[str, str] = field(default_factory=dict)
    confirm_keywords: list[str] = field(default_factory=list)
    reschedule_keywords: list[str] = field(default_factory=list)

    def template(self, key: str) -> str:
        try:
            return self.templates[key]
        except KeyError as exc:
            raise SlotfillError(
                f"Pack '{self.name}' has no template named '{key}'"
            ) from exc


def load_pack(path: str | Path) -> Pack:
    """Load and validate a vertical pack YAML file."""
    path = Path(path)
    if not path.exists():
        raise SlotfillError(f"Pack file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SlotfillError(f"Pack file {path} must contain a YAML mapping")
    for key in ("name", "templates"):
        if key not in raw:
            raise SlotfillError(f"Pack file {path} is missing required key '{key}'")
    rules = [
        ReminderRule(offset=str(r["offset"]), template=str(r.get("template", "reminder")))
        for r in raw.get("reminders", [])
    ]
    keywords = raw.get("keywords", {}) or {}
    return Pack(
        name=str(raw["name"]),
        vertical=str(raw.get("vertical", raw["name"])),
        offer_expiry_minutes=int(raw.get("offer_expiry_minutes", 30)),
        max_offers=int(raw.get("max_offers", 3)),
        reminders=rules,
        templates={str(k): str(v) for k, v in raw["templates"].items()},
        confirm_keywords=[str(k).lower() for k in keywords.get("confirm", [])],
        reschedule_keywords=[str(k).lower() for k in keywords.get("reschedule", [])],
    )


@dataclass
class Settings:
    db_path: str = "slotfill.db"
    waitlist_path: str = "examples/waitlist.csv"
    pack_path: str = "packs/clinic.yaml"
    business_name: str = "Your Business"

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "Settings":
        env = os.environ if environ is None else environ
        return cls(
            db_path=env.get("SLOTFILL_DB", cls.db_path),
            waitlist_path=env.get("SLOTFILL_WAITLIST", cls.waitlist_path),
            pack_path=env.get("SLOTFILL_PACK", cls.pack_path),
            business_name=env.get("SLOTFILL_BUSINESS_NAME", cls.business_name),
        )
