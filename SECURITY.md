# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |
| < 0.1 | No |

## Reporting a vulnerability

Please do not open a public issue for a security vulnerability.

Use GitHub's private vulnerability reporting on this repository
(Security tab, "Report a vulnerability"), or contact TechAurah via
https://techaurah.com. We aim to acknowledge reports within 3 working days
and to agree a disclosure timeline with the reporter.

## Scope notes

SlotFill handles client contact details (names, email addresses) and
appointment data. In v0.1:

- The default notifier is a dry-run log notifier: nothing is sent anywhere
  unless you deliberately configure the email notifier.
- Credentials are read from environment variables only. Never commit a real
  `.env` file; `.env.example` ships with dummy values only.
- The SQLite state store contains message and offer logs. Treat the database
  file as sensitive business data and keep it out of version control (it is
  covered by `.gitignore`).
