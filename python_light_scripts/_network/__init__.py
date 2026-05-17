"""ISOLATED: code that performs network calls and/or needs credentials.

Modules here are kept out of the top-level namespace and excluded from the
default test run because they cannot run offline. No new network calls are
introduced anywhere else in this repository.

See ``python_light_scripts/_network/README.md``.
"""
