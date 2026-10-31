"""SMTP email notifier (the one live channel in v0.1).

Configuration comes from the constructor or the environment:
SLOTFILL_SMTP_HOST, SLOTFILL_SMTP_PORT, SLOTFILL_SMTP_USER,
SLOTFILL_SMTP_PASSWORD, SLOTFILL_SMTP_FROM.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from .base import Notifier, NotifierNotConfiguredError, SentMessage


class EmailNotifier(Notifier):
    def __init__(self, host: str | None = None, port: int | None = None,
                 username: str | None = None, password: str | None = None,
                 from_address: str | None = None, use_tls: bool = True):
        self.host = host or os.environ.get("SLOTFILL_SMTP_HOST", "")
        self.port = int(port or os.environ.get("SLOTFILL_SMTP_PORT", "587"))
        self.username = username or os.environ.get("SLOTFILL_SMTP_USER", "")
        self.password = password or os.environ.get("SLOTFILL_SMTP_PASSWORD", "")
        self.from_address = from_address or os.environ.get("SLOTFILL_SMTP_FROM", "")
        self.use_tls = use_tls

    def _require_config(self) -> None:
        if not self.host or not self.from_address:
            raise NotifierNotConfiguredError(
                "Email notifier is not configured. Set SLOTFILL_SMTP_HOST and "
                "SLOTFILL_SMTP_FROM (see .env.example), or use the default "
                "dry-run log notifier."
            )

    def send(self, recipient: str, subject: str, body: str,
             kind: str = "message") -> SentMessage:
        self._require_config()
        msg = EmailMessage()
        msg["From"] = self.from_address
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password)
            smtp.send_message(msg)
        return SentMessage(recipient=recipient, subject=subject, body=body, kind=kind)
