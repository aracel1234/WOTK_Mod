# Security policy

## Credentials

Do not commit game accounts, email addresses, passwords, browser session data, API keys, or other
secrets. The application intentionally keeps Auto Login account credentials in memory and the
normal **Save Profile** action stores browser settings and coordinates only.

If a secret has ever been committed, deleting it from the latest file is not enough. Rotate the
credential and remove it from Git history before publishing the repository.

## Reports

When reporting a bug, remove personal paths, usernames, account names, and screenshots containing
private information. Include only the minimum configuration needed to reproduce the issue.
