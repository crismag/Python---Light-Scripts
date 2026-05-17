"""Run several subprocess commands concurrently, then post-process.

Migrated from ``multi_threaded/launcher.py``.

HARDENING (Phase 3):
  - ``shell=True`` is removed. Commands must be given as argument lists
    (e.g. ``["sleep", "1"]``), which eliminates shell-injection.
  - The original join logic was broken: a single shared ``Event`` meant the
    final ``event.wait()`` loop returned after the *first* process finished.
    This version waits on every process directly.
"""

import subprocess
import threading


def run_commands(commands, post_processing):
    """Start every command concurrently, wait for all, then post-process.

    Args:
        commands: an iterable of argument lists, e.g. ``[["sleep", "1"], ...]``.
            A plain string is rejected to avoid accidental shell usage.
        post_processing: zero-arg callable run once all processes have exited.

    Returns:
        list[int]: the return code of each process, in input order.
    """
    processes = []
    for command in commands:
        if isinstance(command, str):
            raise TypeError(
                "run_commands expects argument lists, not shell strings; "
                f"got {command!r}. Pass e.g. ['sleep', '1']."
            )
        processes.append(subprocess.Popen(command))  # noqa: S603 (no shell)

    def process_monitor():
        for process in processes:
            process.wait()
        post_processing()

    monitor = threading.Thread(target=process_monitor)
    monitor.start()

    return_codes = [process.wait() for process in processes]
    monitor.join()
    return return_codes
