"""Each source adapter against its synthetic fixture pages (tests/fixtures/sampling)."""

from datetime import date
from pathlib import Path

import pytest

from semval.sampling.adapters import (
    ADAPTERS,
    conversation,
    efsyn,
    guardian,
    standard,
    tanea,
    tovima,
)
from semval.sampling.article import Genre, OutOfScope
from semval.sampling.parsing import soup
from semval.sources import USABLE_ACCESS, is_open, load_sources

FIXTURES = Path(__file__).parent / "fixtures" / "sampling"
REGISTRY = Path(__file__).resolve().parents[1] / "data" / "sources" / "sources.yaml"


def page(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_registry_has_open_usable_entry_for_each_adapter() -> None:
    sources = {s.id: s for s in load_sources(REGISTRY)}
    for sid in ADAPTERS:
        assert is_open(sources[sid]), sid
        assert sources[sid].access in USABLE_ACCESS, sid


def test_tovima_parse() -> None:
    url = "https://www.tovima.gr/2025/03/04/opinions/proto-arthro/"
    art = ADAPTERS["gr-tovima-website"].parse(url, page("tovima_article.html"))
    assert art.title == "Ένας συνθετικός τίτλος"
    assert art.date == date(2025, 3, 4)
    assert art.genre == Genre.OPINION
    # Unclosed <p> tags, the ad box and the "preferred source" link are handled.
    assert art.text.split("\n\n") == [
        "Πρώτη συνθετική παράγραφος για δοκιμή.",
        "Δεύτερη παράγραφος με σύνδεσμο μέσα.",
        "Τρίτη και τελευταία παράγραφος.",
    ]
    assert tovima.genre_of("https://www.tovima.gr/print/stiles/x/y/") == Genre.COLUMNS
    assert tovima.genre_of("https://www.tovima.gr/2025/03/04/politics/x/") == "other"


def test_tovima_listing() -> None:
    assert tovima.page_items(soup(page("tovima_listing.html"))) == [
        ("https://www.tovima.gr/2025/03/04/opinions/proto-arthro/", date(2025, 3, 4)),
        ("https://www.tovima.gr/print/opinions/deytero-arthro/", date(2025, 3, 3)),
    ]
    assert tovima.page_url(1) == "https://www.tovima.gr/category/opinions/"
    assert tovima.page_url(7) == "https://www.tovima.gr/category/opinions/page/7/"


def test_tanea_parse() -> None:
    url = "https://www.tanea.gr/print/2024/06/10/opinions/proti/"
    art = ADAPTERS["gr-tanea-website"].parse(url, page("tanea_article.html"))
    assert art.title == "Συνθετική άποψη"
    assert art.date == date(2024, 6, 10)
    assert art.genre == Genre.OPINION
    assert art.text.split("\n\n") == [
        "Η πρώτη παράγραφος της δοκιμής.",
        "1. Ένα αριθμημένο σημείο.",
        "Ο συγγραφέας είναι φανταστικός.",
    ]


def test_tanea_listing_uses_item_list_only() -> None:
    assert tanea.page_items(soup(page("tanea_listing.html"))) == [
        ("https://www.tanea.gr/print/2024/06/10/opinions/proti/", date(2024, 6, 10)),
        ("https://www.tanea.gr/2024/06/09/opinions/deyteri/", date(2024, 6, 9)),
    ]


def test_efsyn_parse() -> None:
    url = "https://www.efsyn.gr/stiles/1400001/proti-stili/"
    art = ADAPTERS["gr-efsyn-website"].parse(url, page("efsyn_article.html"))
    assert art.title == "Συνθετική στήλη"
    assert art.date == date(2025, 11, 18)
    assert art.genre == Genre.OPINION
    assert art.text.split("\n\n") == [
        "Πρώτη παράγραφος.",
        "Δεύτερη παράγραφος.",
        "Τρίτη παράγραφος μετά τη διαφήμιση.",
    ]
    assert efsyn.genre_of(url, "Η άποψη της ΕφΣυν") == Genre.EDITORIAL
    assert efsyn.genre_of(url, "Στήλες") == Genre.COLUMNS


def test_efsyn_listing() -> None:
    assert efsyn.page_items(soup(page("efsyn_listing.html"))) == [
        ("https://www.efsyn.gr/stiles/1400001/proti-stili/", date(2025, 11, 18)),
        ("https://www.efsyn.gr/stiles/1400000/deyteri-stili/", date(2025, 11, 17)),
        ("https://www.efsyn.gr/stiles/apopseis/400001_palia-morfi/", date(2024, 11, 16)),
    ]
    assert efsyn.page_url(3) == "https://www.efsyn.gr/stiles/apopseis/page/3/"


def test_guardian_parse() -> None:
    url = "https://www.theguardian.com/commentisfree/2024/jan/15/why-tests-matter"
    art = ADAPTERS["gb-guardian-website"].parse(url, page("guardian_article.html"))
    assert art.title == "A synthetic view on testing"
    assert art.date == date(2024, 1, 15)
    assert art.genre == Genre.OPINION
    assert art.text.split("\n\n") == [
        "The first synthetic paragraph argues a point.",
        "The second synthetic paragraph – with an entity.",
        "A. Writer is a fictional columnist",
    ]
    editorial = url.replace("why-tests-matter", "the-guardian-view-on-tests")
    assert guardian.genre_of(editorial) == Genre.EDITORIAL


def test_guardian_day_listing() -> None:
    assert guardian.day_url(date(2024, 1, 5)) == (
        "https://www.theguardian.com/commentisfree/2024/jan/05/all"
    )
    assert guardian.day_items(soup(page("guardian_day.html"))) == [
        "https://www.theguardian.com/commentisfree/2024/jan/15/the-guardian-view-on-tests-they-matter",
        "https://www.theguardian.com/commentisfree/2024/jan/15/why-tests-matter",
    ]


def test_standard_parse() -> None:
    url = "https://www.standard.co.uk/comment/tests-should-pass-b1000001.html"
    art = ADAPTERS["gb-evening-standard"].parse(url, page("standard_article.html"))
    assert art.title == "The Standard View: Tests should pass"
    assert art.date == date(2024, 1, 15)
    assert art.genre == Genre.EDITORIAL
    assert art.text.split("\n\n") == [
        "First synthetic leader paragraph.",
        "Second synthetic leader paragraph.",
    ]


def test_standard_day_listing() -> None:
    assert standard.day_url(date(2024, 1, 15)) == "https://www.standard.co.uk/archive/2024-01-15"
    assert standard.day_items(soup(page("standard_day.html"))) == [
        "https://www.standard.co.uk/comment/tests-should-pass-b1000001.html",
        "https://www.standard.co.uk/comment/a-column-on-testing-b1000002.html",
    ]


def test_conversation_parse() -> None:
    url = "https://theconversation.com/synthetic-piece-on-testing-296001"
    adapter = ADAPTERS["gb-conversation-uk"]
    art = adapter.parse(url, page("conversation_article.html"))
    assert art.title == "Synthetic academics explain tests"
    assert art.date == date(2025, 11, 18)
    assert art.genre == Genre.OPINION
    assert art.text.split("\n\n") == [
        "An explanatory synthetic paragraph.",
        "A second synthetic paragraph with a source.",
    ]
    other_edition = page("conversation_article.html").replace('content="uk"', 'content="au"')
    with pytest.raises(OutOfScope):
        adapter.parse(url, other_edition)


def test_conversation_listing() -> None:
    assert conversation.page_items(soup(page("conversation_listing.html"))) == [
        ("https://theconversation.com/synthetic-piece-on-testing-296001", date(2025, 11, 17)),
        ("https://theconversation.com/another-synthetic-piece-295999", None),
    ]
    assert conversation.page_url(4) == "https://theconversation.com/uk/politics/articles?page=4"
