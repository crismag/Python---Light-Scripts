"""Demo: run a subprocess under a tqdm progress bar."""

from python_light_scripts.process.progress import run_with_progress

if __name__ == "__main__":
    # A short command that emits an info line the helper will surface.
    rc = run_with_progress(
        ["sh", "-c", "echo '-I- starting'; sleep 1; echo '-I- done'"],
        desc="Demo task",
    )
    print(f"return code: {rc}")
