"""CLI: run a command, with a reminder when today is a configured holiday.

Replaces the module-scope logic of the original ``monitoring/holiday.py``.
"""

import argparse

from python_light_scripts.monitoring import holidays

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a command with a holiday reminder.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    parser.add_argument("--holiday-file", default=holidays.DEFAULT_HOLIDAY_FILE)
    parser.add_argument("--profile", default=holidays.DEFAULT_PROFILE)
    args = parser.parse_args()

    # Command is passed as an argument list (no shell) — see run_command().
    holidays.run_with_holiday_check(
        args.command,
        holiday_file=args.holiday_file,
        profile=args.profile,
    )
