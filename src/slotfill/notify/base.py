"""Notifier interface, plus the dry-run log notifier (the v0.1 default).

SlotFill's safety posture: a channel goes live only through an explicit
adapter with its own configuration and compliance review. The default
notifier therefore sends nothing anywhere; it logs what would be sent.
WhatsApp and SMS adapters implement this same interface later; see
docs/notifiers.md for the contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class NotifierNotConfiguredError(RuntimeError):
    """Raised when a notifier is used without the configuration it needs."""


@dataclass
class SentMessage:
    recipient: str
    subject: str
    body: str
    kind: str = "message"


class Notifier(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, body: str,
             kind: str = "message") -> SentMessage:
        """Deliver (or, for dry-run adapters, record) one message."""


@dataclass
class LogNotifier(Notifier):
    """Dry-run notifier: records and prints messages, delivers nothing."""

    sent: list[SentMessage] = field(default_factory=list)
    echo: bool = True

    def send(self, recipient: str, subject: str, body: str,
             kind: str = "message") -> SentMessage:
        msg = SentMessage(recipient=recipient, subject=subject, body=body, kind=kind)
        self.sent.append(msg)
        if self.echo:
            print(f"  [notify:{kind}] To: {recipient}")
            print(f"  Subject: {subject}")
            print(f"  {body}")
        return msg
