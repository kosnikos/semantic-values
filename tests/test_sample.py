"""collect_sample with a fake adapter and a fake transport (no network)."""

import hashlib
from collections.abc import Iterable
from datetime import date
from pathlib import Path

import pytest
import yaml

from conftest import make_source
from semval.sampling.adapters.base import Genre, ParsedArticle
from semval.sampling.fetch import FetchOutcome, PoliteFetcher, Response
from semval.sampling.sample import collect_sample, doc_id_for, doc_text_path
from semval.units import Document

SINCE, UNTIL = date(2024, 1, 1), date(2026, 11, 19)
BODY = "This synthetic sentence must never reach the committed sample. " * 20


class FakeAdapter:
    """Lists /a1../aN on a host; /old is out of range, /news is the wrong genre."""

    def __init__(self, source_id: str, host: str, n: int) -> None:
        self.source_id = source_id
        self.host = host
        self.n = n

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterable[str]:
        yield f"https://{self.host}/old"
        yield f"https://{self.host}/news"
        yield f"https://{self.host}/paid"
        for i in range(self.n):
            yield f"https://{self.host}/a{i}"

    def parse(self, url: str, html: str) -> ParsedArticle:
        path = url.rsplit("/", 1)[1]
        day = date(2020, 1, 1) if path == "old" else date(2025, 3, 4)
        genre = "news" if path == "news" else Genre.OPINION
        return ParsedArticle(title=f"Title {path}", date=day, genre=genre, text=BODY + path)


def transport_for(hosts: list[str]):
    def transport(url: str, headers: dict[str, str]) -> Response:
        if url.endswith("/robots.txt"):
            return Response(200, "User-agent: *\nDisallow:\n")
        if url.endswith("/paid"):
            return Response(200, '<script type="application/ld+json">'
                                 '{"isAccessibleForFree": false}</script>')  # fmt: skip
        return Response(200, "<html>synthetic</html>")

    return transport


class NoClock:
    def now(self) -> float:
        return 0.0

    def sleep(self, seconds: float) -> None:
        pass


def setup(tmp_path: Path, sources: list[dict]) -> dict:
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump(sources), encoding="utf-8")
    fetcher = PoliteFetcher(
        "test-agent/0", cache_dir=tmp_path / "http", transport=transport_for([]), clock=NoClock()
    )
    return {
        "registry_path": registry,
        "fetcher": fetcher,
        "raw_dir": tmp_path / "raw" / "docs",
        "samples_dir": tmp_path / "samples",
    }


def test_collect_rejects_closed_source(tmp_path: Path) -> None:
    sources = [
        make_source(id="fr-closed", country="FR", restriction_scope="tdm_all"),
        make_source(id="gr-paywall", country="GR", access="paywall"),
    ]
    kw = setup(tmp_path, sources)
    adapters = {s["id"]: FakeAdapter(s["id"], "a.test", 3) for s in sources}
    for sid in ["fr-closed", "gr-paywall"]:
        with pytest.raises(ValueError, match=sid):
            collect_sample([sid], 2, SINCE, UNTIL, name="t", adapters=adapters, **kw)
    assert not (tmp_path / "samples").exists()


def test_collect_rejects_source_without_adapter(tmp_path: Path) -> None:
    kw = setup(tmp_path, [make_source(id="gr-a")])
    with pytest.raises(ValueError, match="gr-a"):
        collect_sample(["gr-a"], 2, SINCE, UNTIL, name="t", adapters={}, **kw)


def test_sample_yaml_has_no_text(tmp_path: Path) -> None:
    sources = [
        make_source(id="gr-a", country="GR", languages=["el"]),
        make_source(
            id="gb-a",
            country="GB",
            languages=["en"],
            restriction_scope="tdm_all",
            access_method="scrape",
        ),
    ]
    kw = setup(tmp_path, sources)
    adapters = {
        "gr-a": FakeAdapter("gr-a", "gr.test", 5),
        "gb-a": FakeAdapter("gb-a", "gb.test", 5),
    }
    manifest = collect_sample(["gr-a", "gb-a"], 3, SINCE, UNTIL, name="t", adapters=adapters, **kw)

    out = tmp_path / "samples" / "t.yaml"
    raw = out.read_text(encoding="utf-8")
    assert "synthetic sentence" not in raw
    data = yaml.safe_load(raw)
    docs = [Document(**d) for d in data["documents"]]
    assert len(docs) == 6
    assert {d.country for d in docs} == {"GR", "GB"}
    assert all(set(d) <= set(Document.model_fields) for d in data["documents"])
    for doc in docs:
        assert doc.id == doc_id_for(doc.source_id, doc.url)
        assert doc.genre == "opinion"
        assert doc.date == date(2025, 3, 4)
        text = doc_text_path(kw["raw_dir"], doc.id).read_text(encoding="utf-8")
        assert text.startswith(BODY)
        assert doc.text_sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert [d.language for d in docs if d.country == "GR"] == ["el"] * 3

    stats = manifest.stats["gr-a"]
    assert stats[FetchOutcome.NOT_FREE] == 1
    assert stats["out_of_range"] == 1
    assert stats["wrong_genre"] == 1
    assert stats["kept"] == 3


def test_shortfall_moves_to_next_source(tmp_path: Path) -> None:
    sources = [make_source(id="gr-a"), make_source(id="gr-b")]
    kw = setup(tmp_path, sources)
    adapters = {
        "gr-a": FakeAdapter("gr-a", "a.test", 1),
        "gr-b": FakeAdapter("gr-b", "b.test", 10),
    }
    manifest = collect_sample(["gr-a", "gr-b"], 6, SINCE, UNTIL, name="t", adapters=adapters, **kw)
    counts = {sid: sum(d.source_id == sid for d in manifest.documents) for sid in adapters}
    assert counts == {"gr-a": 1, "gr-b": 5}


def test_doc_id_and_path() -> None:
    url = "https://a.test/x"
    doc_id = doc_id_for("gr-a", url)
    assert doc_id == "gr-a:" + hashlib.sha1(url.encode()).hexdigest()[:12]
    # The file name avoids ":" (not allowed in Windows file names).
    assert ":" not in doc_text_path(Path("raw"), doc_id).name


def test_cli_sample_selects_sources_by_country(tmp_path: Path, monkeypatch) -> None:
    import semval.sampling.sample as sample_mod
    from semval.cli import main

    calls: dict = {}

    def fake_collect(source_ids, per_country, since, until, **kw):
        calls.update(source_ids=list(source_ids), per_country=per_country, since=since,
                     until=until, name=kw["name"], budget=kw["fetcher"].max_requests)  # fmt: skip
        return sample_mod.SampleManifest(
            name=kw["name"], since=since, until=until, per_country=per_country, requests=0,
            stats={}, documents=[],
        )  # fmt: skip

    monkeypatch.setattr(sample_mod, "collect_sample", fake_collect)
    argv = ["sample", "--countries", "GR", "--per-country", "4", "--since", "2024-01-01",
            "--until", "2024-12-31", "--name", "t", "--max-requests", "9"]  # fmt: skip
    assert main(argv) == 0
    assert calls["source_ids"] == ["gr-tovima-website", "gr-tanea-website", "gr-efsyn-website"]
    assert (calls["per_country"], calls["name"], calls["budget"]) == (4, "t", 9)
    assert (calls["since"], calls["until"]) == (date(2024, 1, 1), date(2024, 12, 31))


def test_gives_up_after_attempt_cap(tmp_path: Path) -> None:
    class AllPaid(FakeAdapter):
        def list_candidates(self, fetcher, since, until):
            i = 0
            while True:  # an endless listing must not mean endless requests
                i += 1
                yield f"https://{self.host}/{i}/paid"

    kw = setup(tmp_path, [make_source(id="gr-a")])
    manifest = collect_sample(
        ["gr-a"], 2, SINCE, UNTIL, name="t", adapters={"gr-a": AllPaid("gr-a", "a.test", 0)}, **kw
    )
    assert manifest.documents == []
    assert manifest.stats["gr-a"] == {"not_free": 6}
