"""ISOLATED: Windows-only code.

Modules in this package import Windows-only libraries (``winreg``,
``win32com``, ``comtypes``) and will NOT import on Linux/macOS. They are
deliberately kept out of the top-level package namespace and are excluded
from the default test run.

Import them explicitly and only on Windows, e.g.::

    from python_light_scripts._windows import registry_secret

See ``python_light_scripts/_windows/README.md``.
"""
