"""ISOLATED / Windows-only: read & write a value in the Windows registry.

Migrated from ``windows/store_pass_in_registry.py``.

WARNING: The Windows registry is NOT a secure secret store. Values written
here are readable by any process running as the same user. The hardcoded
password in the original has been removed; the value is now passed in.
See ``SECURITY.md``.

This module imports ``winreg`` and will fail to import off Windows.
"""

import winreg

SUBKEY = r"Software\MyApp"
VALUE_NAME = "password"


def store_value(value, subkey=SUBKEY, value_name=VALUE_NAME):
    """Write ``value`` under ``HKEY_CURRENT_USER\\<subkey>``."""
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey)
    try:
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
    finally:
        winreg.CloseKey(key)


def read_value(subkey=SUBKEY, value_name=VALUE_NAME):
    """Read a value from ``HKEY_CURRENT_USER\\<subkey>``."""
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return value
    finally:
        winreg.CloseKey(key)
