"""RFC 9309 robots.txt rules: wildcards, longest match, our own group, Crawl-delay."""

from semval.sampling.robots import parse_robots, product_token

UA = "semval-research/0.1 (+https://example.org)"
TXT = """
Sitemap: https://a.test/sitemap.xml
User-agent: *
Disallow: /discussion/*
Disallow: /*?commentpage=
Disallow: /*/print$
Allow: /discussion/public/
Crawl-delay: 3

User-agent: OtherBot
User-agent: SEMVAL-research
Disallow: /secret
Crawl-delay: 9
"""


def test_product_token() -> None:
    assert product_token(UA) == "semval-research"


def test_wildcards_and_longest_match_for_star_group() -> None:
    rules = parse_robots(TXT.replace("SEMVAL-research", "someone-else"), UA)
    assert rules.sitemaps == ["https://a.test/sitemap.xml"]
    assert rules.crawl_delay == 3
    assert not rules.can_fetch("https://a.test/discussion/x")
    assert rules.can_fetch("https://a.test/discussion/public/x")  # longer Allow wins
    assert not rules.can_fetch("https://a.test/news/x?commentpage=2")
    assert not rules.can_fetch("https://a.test/news/x/print")
    assert rules.can_fetch("https://a.test/news/x/print/more")  # "$" anchors the end
    assert rules.can_fetch("https://a.test/news/x")


def test_our_group_replaces_star_group() -> None:
    rules = parse_robots(TXT, UA)
    assert rules.crawl_delay == 9
    assert not rules.can_fetch("https://a.test/secret/page")
    assert rules.can_fetch("https://a.test/discussion/x")  # the * group does not apply


def test_leading_bom_is_ignored() -> None:
    rules = parse_robots("﻿User-agent: *\nDisallow: /private/\n", UA)
    assert not rules.can_fetch("https://a.test/private/x")
    assert rules.can_fetch("https://a.test/public/x")


def test_empty_disallow_allows_all() -> None:
    assert parse_robots("User-agent: *\nDisallow:\n", UA).can_fetch("https://a.test/x")
