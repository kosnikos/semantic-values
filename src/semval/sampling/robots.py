"""robots.txt rules for one user-agent, per RFC 9309.

The stdlib ``urllib.robotparser`` reads ``*`` and ``$`` in paths literally and applies the
first matching rule, so it misses rules such as ``Disallow: /*?commentpage=``. This parser
supports both wildcards, uses the longest match (``Allow`` wins a tie), merges every group
that names our product token (else the ``*`` groups), and reads ``Crawl-delay``.
"""

import re
from dataclasses import dataclass, field
from urllib.parse import unquote, urlsplit


@dataclass(frozen=True)
class Rule:
    allow: bool
    path: str
    pattern: re.Pattern[str]


@dataclass
class RobotsRules:
    rules: list[Rule] = field(default_factory=list)
    crawl_delay: float | None = None
    sitemaps: list[str] = field(default_factory=list)
    disallow_all: bool = False

    def can_fetch(self, url: str) -> bool:
        if self.disallow_all:
            return False
        parts = urlsplit(url)
        target = unquote(parts.path or "/") + (f"?{unquote(parts.query)}" if parts.query else "")
        best: Rule | None = None
        for rule in self.rules:
            if not rule.pattern.match(target):
                continue
            longer = best is None or len(rule.path) > len(best.path)
            tie_allow = best is not None and len(rule.path) == len(best.path) and rule.allow
            if longer or tie_allow:
                best = rule
        return best is None or best.allow


def _compile(path: str) -> re.Pattern[str]:
    anchored = path.endswith("$")
    body = re.escape(unquote(path.rstrip("$"))).replace(r"\*", ".*")
    return re.compile(body + ("$" if anchored else ""))


def product_token(user_agent: str) -> str:
    """``semval-research/0.1 (+url)`` -> ``semval-research``."""
    return user_agent.split("/")[0].split()[0].lower()


def parse_robots(text: str, user_agent: str) -> RobotsRules:
    token = product_token(user_agent)
    groups: list[tuple[list[str], list[Rule], list[float]]] = []
    sitemaps: list[str] = []
    agents: list[str] = []
    rules: list[Rule] = []
    delays: list[float] = []
    in_rules = False
    text = text.removeprefix("﻿")  # a UTF-8 BOM would hide the first User-agent line
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (s.strip() for s in line.split(":", 1))
        key = key.lower()
        if key == "sitemap":
            sitemaps.append(value)
        elif key == "user-agent":
            if in_rules:  # a user-agent line after rules starts a new group
                groups.append((agents, rules, delays))
                agents, rules, delays, in_rules = [], [], [], False
            agents.append(value.lower())
        elif key in ("allow", "disallow"):
            in_rules = True
            if value:
                rules.append(Rule(key == "allow", value, _compile(value)))
        elif key == "crawl-delay":
            in_rules = True
            try:
                delays.append(float(value))
            except ValueError:
                pass
    groups.append((agents, rules, delays))
    ours = [g for g in groups if token in g[0]]
    chosen = ours or [g for g in groups if "*" in g[0]]
    merged = [r for g in chosen for r in g[1]]
    delay = max((d for g in chosen for d in g[2]), default=None)
    return RobotsRules(rules=merged, crawl_delay=delay, sitemaps=sitemaps)
