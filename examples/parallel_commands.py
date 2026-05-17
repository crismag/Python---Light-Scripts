"""Demo: run several commands concurrently, then post-process.

Replaces the broken ``multi_threaded/test.py`` (which never imported
``run_commands`` and used hardcoded absolute paths).
"""

from python_light_scripts.process.parallel import run_commands

if __name__ == "__main__":
    # Commands are argument lists (no shell) — see run_commands() hardening.
    commands = [
        ["sleep", "0.2"],
        ["sleep", "0.3"],
        ["sleep", "0.1"],
    ]

    def post_processing():
        print("All commands completed; post-processing done.")

    run_commands(commands, post_processing)
