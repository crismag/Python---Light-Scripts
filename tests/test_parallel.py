"""Tests for process.parallel — no-shell execution and correct join."""

import pytest

from python_light_scripts.process.parallel import run_commands


def test_string_command_rejected_to_prevent_shell_use():
    # A bare string would historically have been run with shell=True.
    with pytest.raises(TypeError):
        run_commands(["echo hello"], lambda: None)


def test_all_processes_complete_before_post_processing():
    calls = []

    def post():
        calls.append("done")

    codes = run_commands([["true"], ["true"], ["false"]], post)

    # post_processing ran exactly once, after every process finished...
    assert calls == ["done"]
    # ...and every process was actually waited on (return codes collected).
    assert codes == [0, 0, 1]
