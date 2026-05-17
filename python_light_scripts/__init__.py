"""Python Light Scripts — a cookbook of small, reusable Python utilities.

Importable subpackages (cross-platform, safe to import):

- ``geometry``   — point transforms and image generation
- ``excel``      — Excel-to-JSON readers
- ``xmltools``   — XML reformatting helpers
- ``monitoring`` — date/holiday-aware command running
- ``acl``        — POSIX ACL management (Linux runtime, import-safe everywhere)
- ``auth``       — TOTP and session-token helpers
- ``process``    — subprocess orchestration helpers

Isolated subpackages (do NOT import automatically — platform/credential bound):

- ``_windows``   — Windows-only code (winreg, Outlook COM)
- ``_network``   — code that performs network calls / needs credentials

See ``README.md`` and ``SECURITY.md`` at the repository root.
"""

__version__ = "0.1.0"
