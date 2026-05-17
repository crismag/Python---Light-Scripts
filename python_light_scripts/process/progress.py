"""Run a subprocess while showing a tqdm progress bar.

Reconstructed from ``command_line_tqdm_progressbar_demo.py``. The original
was an incomplete snippet referencing undefined helpers (``iprint``,
``fatal_error``, ``safe_open``); this is a self-contained, runnable version
that preserves the original intent: stream a process's ``-I-`` info lines
above an indeterminate progress bar.
"""

import subprocess
import time

from tqdm import tqdm


def run_with_progress(cmd, desc="Running", info_prefix="-I-", tick=0.01):
    """Run ``cmd`` (a list of args), animating a progress bar until it exits.

    Lines beginning with ``info_prefix`` are printed above the bar. Returns
    the process return code.
    """
    # `cmd` must be an argument list (no shell); callers control it.
    proc = subprocess.Popen(  # noqa: S603
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    )

    with tqdm(
        total=100,
        desc=desc,
        bar_format="{desc} |{bar}| {percentage:3.0f}% {elapsed}s",
        ncols=80,
        colour="magenta",
    ) as progress_bar:
        i = 0
        while proc.poll() is None:
            line = proc.stdout.readline() if proc.stdout else ""
            if line and line.startswith(info_prefix):
                tqdm.write(line.strip())
            progress_bar.update(1 if i < 99 else 0)
            i += 1
            time.sleep(tick)
        progress_bar.n = 100
        progress_bar.refresh()

    return proc.returncode
