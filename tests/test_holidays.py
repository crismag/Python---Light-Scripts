"""Tests for python_light_scripts.monitoring.holidays."""

from pathlib import Path

import pytest

from python_light_scripts.monitoring import holidays

DATA = Path(__file__).parent / "data"
SAMPLE = str(DATA / "holidays_sample.conf")


def test_load_holidays_parses_dates_only():
    loaded = holidays.load_holidays(SAMPLE)
    assert loaded == {"01/01/2026", "07/04/2026", "12/25/2026"}


def test_today_string_format():
    s = holidays.today_string()
    assert len(s) == 10 and s.count("/") == 2


def test_is_holiday_true_and_false():
    assert holidays.is_holiday("12/25/2026", SAMPLE) is True
    assert holidays.is_holiday("06/15/2026", SAMPLE) is False


def test_run_command_rejects_shell_string():
    # A bare string would historically have been passed to os.system().
    with pytest.raises(TypeError):
        holidays.run_command("echo hi; rm -rf /")


def test_run_command_executes_argument_list():
    rc = holidays.run_command(["true"], profile="/nonexistent/profile")
    assert rc == 0


def test_run_with_holiday_check_returns_command_rc():
    rc = holidays.run_with_holiday_check(
        ["false"], holiday_file=SAMPLE, profile="/nonexistent/profile"
    )
    assert rc == 1
