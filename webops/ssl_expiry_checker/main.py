"""Check TLS certificate expiry dates."""

from __future__ import annotations

import argparse
import json
import socket
import ssl
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class SslResult:
    host: str
    port: int
    ok: bool
    expires_at: str | None
    days_remaining: int | None
    warning: str | None = None
    error: str | None = None


def load_hosts(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("YAML input requires pyyaml.") from exc
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            items = data.get("hosts", data) if isinstance(data, dict) else data
            return [str(item) for item in items]
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    return [value]


def split_host(value: str, default_port: int) -> tuple[str, int]:
    if ":" in value and not value.startswith("["):
        host, port = value.rsplit(":", 1)
        return host, int(port)
    return value, default_port


def check_host(value: str, default_port: int, timeout: float, warn_days: int) -> SslResult:
    host, port = split_host(value, default_port)
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
    except (OSError, ssl.SSLError, ValueError) as exc:
        return SslResult(host, port, False, None, None, error=f"{type(exc).__name__}: {exc}")

    not_after = cert.get("notAfter")
    if not not_after:
        return SslResult(host, port, False, None, None, error="certificate missing notAfter")
    expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
    days = (expires - datetime.now(UTC)).days
    warning = f"expires within {warn_days} days" if days < warn_days else None
    return SslResult(host, port, days >= 0 and warning is None, expires.isoformat(), days, warning)


def print_results(results: list[SslResult]) -> None:
    for result in results:
        outcome = "OK" if result.ok else "WARN" if result.warning else "FAIL"
        detail = result.warning or result.error or f"{result.days_remaining} day(s) remaining"
        print(f"{outcome:4} {result.host}:{result.port} {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check TLS certificate expiry dates.")
    parser.add_argument("input", help="Hostname or input file.")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--warn-days", type=int, default=30)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args(argv)

    try:
        results = [
            check_host(host, args.port, args.timeout, args.warn_days)
            for host in load_hosts(args.input)
        ]
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print_results(results)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    if args.fail_on_warning and any(not r.ok for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
