# Notifiers

Every message SlotFill produces (reminder, offer, booked confirmation,
stand-down, acknowledgements) goes through one small interface:

```python
class Notifier(ABC):
    def send(self, recipient: str, subject: str, body: str,
             kind: str = "message") -> SentMessage: ...
```

`kind` is one of: `reminder`, `offer`, `booked`, `stood_down`,
`confirm_ack`, `reschedule_ack`. The service logs every send to the SQLite
store regardless of which notifier is configured, so switching channels
never loses the audit trail.

## Shipped in v0.1

| Notifier | Behaviour |
|---|---|
| `LogNotifier` (default) | Dry-run. Records and prints what would be sent; delivers nothing. Used by the demo and tests. |
| `EmailNotifier` | Real sends over SMTP (`smtplib`, TLS by default). Configured via the `SLOTFILL_SMTP_*` environment variables; raises a clear `NotifierNotConfiguredError` when they are missing. |

## Adding a channel (WhatsApp, SMS, and friends)

WhatsApp and SMS are deliberately not wired in v0.1. SlotFill's posture,
shared with the other TechAurah open-source projects, is that a channel goes
live only through an explicit adapter with its own compliance review:
opt-in records, template approval where the platform requires it, opt-out
handling, and rate limits. An adapter PR must document:

1. How recipient consent is recorded and checked before a send.
2. How opt-out replies stop all future sends to that contact.
3. Which message templates the channel requires (for example WhatsApp
   template messages) and how pack templates map onto them.
4. Failure behaviour: retries, and how failures land in the store log.

Implement `Notifier.send`, keep the store logging in the service layer
untouched, and add tests using a fake transport. Channel PRs without the
four points above will be asked to add them before review.
