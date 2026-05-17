"""Fetch and inspect robots.txt files."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests


@dataclass
class RobotsSummary:
    robots_url: str
    status_code: int | None
    sitemaps: list[str]
    groups: dict[str, list[str]]
    path_allowed: bool | None
    error: str | None = None


def robots_url_from_input(value: str) -> str:
    parsed = urlparse(value)
    if parsed.path.endswith("/robots.txt"):
        return value
    root = f"{parsed.scheme or 'https'}://{parsed.netloc or parsed.path}"
    return urljoin(root.rstrip("/") + "/", "robots.txt")


def load_inputs(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    return [value]


def parse_groups(text: str) -> tuple[list[str], dict[str, list[str]]]:
    sitemaps: list[str] = []
    groups: dict[str, list[str]] = {}
    current_agents: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        low = key.lower()
        if low == "sitemap":
            sitemaps.append(value)
        elif low == "user-agent":
            current_agents = [value]
            groups.setdefault(value, [])
        elif low in {"allow", "disallow"} and current_agents:
            rule = f"{key}: {value}"
            for agent in current_agents:
                groups.setdefault(agent, []).append(rule)
    return sitemaps, groups


def analyze(value: str, user_agent: str, path: str, timeout: float) -> RobotsSummary:
    robots_url = robots_url_from_input(value)
    try:
        response = requests.get(robots_url, timeout=timeout)
    except requests.RequestException as exc:
        return RobotsSummary(robots_url, None, [], {}, None, f"{type(exc).__name__}: {exc}")

    sitemaps, groups = parse_groups(response.text)
    allowed = None
    if response.ok:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        allowed = parser.can_fetch(user_agent, urljoin(robots_url, path))
    return RobotsSummary(robots_url, response.status_code, sitemaps, groups, allowed)


def print_summary(summary: RobotsSummary) -> None:
    print(f"{summary.robots_url} -> {summary.status_code if summary.status_code is not None else '-'}")
    if summary.error:
        print(f"ERROR: {summary.error}")
        return
    print(f"Sitemaps: {len(summary.sitemaps)}")
    for sitemap in summary.sitemaps:
        print(f"  {sitemap}")
    print(f"User-agent groups: {len(summary.groups)}")
    for agent, rules in summary.groups.items():
        print(f"  {agent}: {len(rules)} rule(s)")
    if summary.path_allowed is not None:
        print(f"Path allowed: {summary.path_allowed}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze robots.txt rules.")
    parser.add_argument("input", help="Site URL or robots.txt URL.")
    parser.add_argument("--user-agent", default="*")
    parser.add_argument("--path", default="/")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    summaries = [
        analyze(value, args.user_agent, args.path, args.timeout)
        for value in load_inputs(args.input)
    ]
    for summary in summaries:
        print_summary(summary)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([asdict(s) for s in summaries], indent=2) + "\n"
        args.json_out.write_text(payload, encoding="utf-8")
    return 0 if all(not summary.error for summary in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
