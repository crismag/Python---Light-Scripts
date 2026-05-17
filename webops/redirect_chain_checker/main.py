"""Inspect URL redirect chains."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests


@dataclass
class RedirectHop:
    url: str
    status_code: int | None
    location: str | None
    error: str | None = None


def load_urls(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    return [value]


def check_chain(url: str, timeout: float, max_hops: int) -> list[RedirectHop]:
    hops: list[RedirectHop] = []
    seen = set()
    current = url
    for _ in range(max_hops + 1):
        if current in seen:
            hops.append(RedirectHop(current, None, None, "redirect_loop_detected"))
            break
        seen.add(current)
        try:
            response = requests.get(current, timeout=timeout, allow_redirects=False)
        except requests.RequestException as exc:
            hops.append(RedirectHop(current, None, None, f"{type(exc).__name__}: {exc}"))
            break
        location = response.headers.get("Location")
        hops.append(RedirectHop(current, response.status_code, location))
        if not (300 <= response.status_code < 400 and location):
            break
        current = urljoin(current, location)
    else:
        hops.append(RedirectHop(current, None, None, f"exceeded max hops: {max_hops}"))
    return hops


def print_chains(chains: dict[str, list[RedirectHop]]) -> None:
    for original, hops in chains.items():
        print(f"\n{original}")
        for index, hop in enumerate(hops, start=1):
            status = hop.status_code if hop.status_code is not None else "-"
            target = f" -> {hop.location}" if hop.location else ""
            print(f"  {index}. {status} {hop.url}{target}")
            if hop.error:
                print(f"     ERROR: {hop.error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect redirect hops for one or more URLs.")
    parser.add_argument("input", help="URL or text file containing URLs.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-hops", type=int, default=10)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    chains = {url: check_chain(url, args.timeout, args.max_hops) for url in load_urls(args.input)}
    print_chains(chains)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        data = {url: [asdict(hop) for hop in hops] for url, hops in chains.items()}
        args.json_out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

