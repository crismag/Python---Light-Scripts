"""Run a command, printing a reminder when today is a configured holiday.

Productionized from ``monitoring/holiday.py``: pure logic separated from the
CLI (which lives in ``examples/holiday_runner.py``), type hints and
docstrings added.

HARDENING (Phase 3): the original used
``os.system("source <profile>; <cmd>")``, where ``<cmd>`` came straight from
``sys.argv`` — an unrestricted shell-injection sink, and ``source`` is a
bash-ism. This version takes the command as an argument list and runs it
through ``bash -c`` with the profile path and command passed as *separate*
argv entries, so neither can inject shell syntax.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Sequence

DEFAULT_HOLIDAY_FILE = "./config/holidays.conf"
DEFAULT_PROFILE = "~/.profile.ADAMUS"

# Sources $1 (profile) then execs the remaining args as the command.
_RUNNER = 'if [ -f "$1" ]; then . "$1"; fi; shift; exec "$@"'


def load_holidays(holiday_file: str = DEFAULT_HOLIDAY_FILE) -> set[str]:
    """Read a holidays config file.

    Blank lines and ``#`` comment lines are ignored. The first
    whitespace-delimited token of each remaining line is taken as an
    ``MM/DD/YYYY`` date; any trailing text (e.g. a label) is discarded.

    Args:
        holiday_file: path to the holidays config file.

    Returns:
        The set of holiday date strings.
    """
    dates: set[str] = set()
    with open(holiday_file) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            dates.add(stripped.split()[0])
    return dates


def today_string() -> str:
    """Return today's date formatted as ``MM/DD/YYYY``.

    The original script mis-unpacked ``time.localtime()`` (and applied stray
    ``+1`` / ``+1900`` offsets), producing a wrong date; this reads the
    struct's named fields directly.
    """
    now = time.localtime()
    return f"{now.tm_mon:02d}/{now.tm_mday:02d}/{now.tm_year:04d}"


def is_holiday(
    date_str: str | None = None,
    holiday_file: str = DEFAULT_HOLIDAY_FILE,
) -> bool:
    """Return whether ``date_str`` (default: today) is a configured holiday."""
    if date_str is None:
        date_str = today_string()
    return date_str in load_holidays(holiday_file)


def run_command(
    cmd: Sequence[str],
    profile: str = DEFAULT_PROFILE,
) -> int:
    """Source ``profile`` (if present), then run ``cmd``.

    Args:
        cmd: the command as an argument list, e.g. ``["ls", "-l"]``. A plain
            string is rejected to avoid reintroducing shell injection.
        profile: a shell profile to source first; ``~`` is expanded.

    Returns:
        The command's return code.

    Raises:
        TypeError: if ``cmd`` is a string rather than an argument list.
    """
    if isinstance(cmd, str):
        raise TypeError(
            "run_command expects an argument list, not a shell string; "
            f"got {cmd!r}. Pass e.g. ['ls', '-l']."
        )
    profile_path = os.path.expanduser(profile)
    args = ["bash", "-c", _RUNNER, "bash", profile_path, *cmd]
    return subprocess.run(args).returncode  # noqa: S603 (no shell, fixed argv)


def run_with_holiday_check(
    cmd: Sequence[str],
    holiday_file: str = DEFAULT_HOLIDAY_FILE,
    profile: str = DEFAULT_PROFILE,
) -> int:
    """Run ``cmd``, printing a reminder first if today is a holiday.

    Returns the command's return code.
    """
    today = today_string()
    if is_holiday(today, holiday_file):
        print(f"[REMINDER] {time.ctime()}: today ({today}) is a holiday")
    else:
        print(f"{time.ctime()}: RUNNING...")

    rc = run_command(cmd, profile=profile)
    print("\n\n")
    return rc
