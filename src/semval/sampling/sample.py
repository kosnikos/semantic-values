"""Collect a small sample of opinion texts per country through the source adapters.

Texts go to the git-ignored raw cache; only Document references are written to the
committed sample file. Source-agnostic: everything source-specific is in the adapters.
"""

import hashlib
import json
import logging
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import date
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from semval.sampling.adapters import ADAPTERS
from semval.sampling.adapters.base import Genre, OutOfScope, ParseError, SourceAdapter
from semval.sampling.fetch import FetchOutcome, PoliteFetcher, RequestBudgetExceeded
from semval.sources import USABLE_ACCESS, Source, is_open, load_sources
from semval.units import Document

log = logging.getLogger(__name__)

DEFAULT_REGISTRY = Path("data/sources/sources.yaml")
DEFAULT_RAW_DIR = Path("data/raw/docs")
DEFAULT_SAMPLES_DIR = Path("data/samples")
MIN_TEXT_CHARS = 600  # shorter "articles" are usually teasers or parse failures
ATTEMPTS_PER_TARGET = 3  # article pages tried per article wanted, before giving up


class Skip(StrEnum):
    """Per-source counters besides the fetch outcomes."""

    KEPT = "kept"
    OUT_OF_RANGE = "out_of_range"
    WRONG_GENRE = "wrong_genre"
    OUT_OF_SCOPE = "out_of_scope"
    PARSE_ERROR = "parse_error"
    TOO_SHORT = "too_short"


class SampleManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    # Collection parameters; None / 0 for samples that were not collected (derived, dataset-made).
    since: date | None = None
    until: date | None = None
    per_country: int = 0
    requests: int = 0
    stopped_early: str | None = None
    stats: dict[str, dict[str, int]]
    documents: list[Document]


def doc_id_for(source_id: str, url: str) -> str:
    return f"{source_id}:{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}"


def doc_text_path(raw_dir: Path, doc_id: str) -> Path:
    """Cached text of a document. ":" is not allowed in Windows file names, so it becomes "__"."""
    return Path(raw_dir) / f"{doc_id.replace(':', '__')}.txt"


def doc_meta_path(raw_dir: Path, doc_id: str) -> Path:
    """Cached metadata (the title) of a document, next to its text."""
    return doc_text_path(raw_dir, doc_id).with_suffix(".meta.json")


def to_reference(doc: Document, raw_dir: Path) -> Document:
    """The committable form of ``doc``: the title moves to the raw cache, only its hash stays.

    Spec section 5.5: only references (URL, date, source, title hash) are committed.
    """
    if doc.title is None:
        return doc
    meta = {"id": doc.id, "url": doc.url, "title": doc.title}
    path = doc_meta_path(raw_dir, doc.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    title_hash = hashlib.sha256(doc.title.encode("utf-8")).hexdigest()
    return doc.model_copy(update={"title": None, "title_sha256": title_hash})


def write_manifest(manifest: SampleManifest, samples_dir: Path) -> Path:
    """Write ``<samples_dir>/<name>.yaml``; documents carry no ``title`` key."""
    data = manifest.model_dump(mode="json", exclude={"documents": {"__all__": {"title"}}})
    samples_dir.mkdir(parents=True, exist_ok=True)
    out = samples_dir / f"{manifest.name}.yaml"
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return out


def derive_sample(base: SampleManifest, name: str, ids: list[str]) -> SampleManifest:
    """A new sample of exactly the documents ``ids`` of ``base``, in that order.

    Texts are shared (same document ids in the raw cache); ValueError names an unknown id.
    """
    by_id = {d.id: d for d in base.documents}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise ValueError(f"not in sample {base.name!r}: {', '.join(unknown)}")
    return base.model_copy(update={"name": name, "documents": [by_id[i] for i in ids], "stats": {}})


def usable_sources(
    source_ids: Iterable[str], registry: list[Source], adapters: Mapping[str, SourceAdapter]
) -> list[Source]:
    """Registry entries for ``source_ids``; ValueError if one is unknown, closed or unusable."""
    by_id = {s.id: s for s in registry}
    out = []
    for sid in source_ids:
        src = by_id.get(sid)
        if src is None:
            raise ValueError(f"unknown source id: {sid}")
        if not is_open(src):
            raise ValueError(f"{sid}: restriction scope {src.restriction_scope!r} is not open")
        if src.access not in USABLE_ACCESS:
            raise ValueError(f"{sid}: access {src.access!r} is not usable")
        if sid not in adapters:
            raise ValueError(f"{sid}: no adapter")
        out.append(src)
    return out


def sources_for_countries(
    countries: Iterable[str], registry: list[Source], adapters: Mapping[str, SourceAdapter]
) -> list[str]:
    """Ids of sources with an adapter in ``countries``, in adapter order."""
    by_id = {s.id: s for s in registry}
    wanted = set(countries)
    return [sid for sid in adapters if sid in by_id and by_id[sid].country in wanted]


def _try_url(
    src: Source,
    adapter: SourceAdapter,
    url: str,
    since: date,
    until: date,
    fetcher: PoliteFetcher,
    raw_dir: Path,
    stats: Counter[str],
) -> Document | None:
    """Fetch and parse one candidate; cache its text and return a Document if it is kept."""
    result = fetcher.get(url)
    if result.outcome is not FetchOutcome.OK or result.html is None:
        stats[result.outcome] += 1
        return None
    try:
        art = adapter.parse(url, result.html)
    except OutOfScope as err:
        log.info("%s: out of scope %s: %s", src.id, url, err)
        stats[Skip.OUT_OF_SCOPE] += 1
        return None
    except ParseError as err:
        log.info("%s: parse error %s: %s", src.id, url, err)
        stats[Skip.PARSE_ERROR] += 1
        return None
    if art.date is None or not since <= art.date <= until:
        stats[Skip.OUT_OF_RANGE] += 1
        return None
    if art.genre not in set(Genre):
        stats[Skip.WRONG_GENRE] += 1
        return None
    if len(art.text) < MIN_TEXT_CHARS:
        stats[Skip.TOO_SHORT] += 1
        return None
    doc_id = doc_id_for(src.id, url)
    path = doc_text_path(raw_dir, doc_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = art.text.encode("utf-8")
    path.write_bytes(data)
    stats[Skip.KEPT] += 1
    doc = Document(
        id=doc_id,
        source_id=src.id,
        country=src.country,
        language=src.languages[0],
        date=art.date,
        genre=str(art.genre),
        url=url,
        title=art.title,
        text_sha256=hashlib.sha256(data).hexdigest(),
    )
    return to_reference(doc, raw_dir)


def _take(
    src: Source,
    adapter: SourceAdapter,
    target: int,
    since: date,
    until: date,
    fetcher: PoliteFetcher,
    raw_dir: Path,
    seen: set[str],
    out: list[Document],
    stats: Counter[str],
) -> None:
    """Append up to ``target`` documents from one source to ``out``.

    Gives up after ``ATTEMPTS_PER_TARGET * target`` article pages. Checks both limits before
    asking the listing for the next URL, which may cost a listing request.
    """
    if target <= 0:
        return
    kept = attempts = 0
    for url in adapter.list_candidates(fetcher, since, until):
        if url in seen:
            continue
        seen.add(url)
        attempts += 1
        doc = _try_url(src, adapter, url, since, until, fetcher, raw_dir, stats)
        if doc is not None:
            out.append(doc)
            kept += 1
            log.info("%s: kept %d/%d %s", src.id, kept, target, url)
        if kept >= target or attempts >= ATTEMPTS_PER_TARGET * target:
            return


def collect_sample(
    source_ids: Iterable[str],
    per_country: int,
    since: date,
    until: date,
    *,
    name: str,
    registry_path: Path = DEFAULT_REGISTRY,
    fetcher: PoliteFetcher | None = None,
    adapters: Mapping[str, SourceAdapter] = ADAPTERS,
    raw_dir: Path = DEFAULT_RAW_DIR,
    samples_dir: Path = DEFAULT_SAMPLES_DIR,
) -> SampleManifest:
    """Collect up to ``per_country`` documents per country; write ``<samples_dir>/<name>.yaml``.

    Within a country, sources share the quota in the order given; a source that falls short
    leaves its shortfall to the sources after it.
    """
    sources = usable_sources(source_ids, load_sources(registry_path), adapters)
    fetcher = fetcher or PoliteFetcher()
    by_country: dict[str, list[Source]] = defaultdict(list)
    for src in sources:
        by_country[src.country].append(src)
    docs: list[Document] = []
    stats: dict[str, Counter[str]] = {s.id: Counter() for s in sources}
    seen: set[str] = set()
    stopped: str | None = None
    try:
        for group in by_country.values():
            remaining = per_country
            for i, src in enumerate(group):
                target = math.ceil(remaining / (len(group) - i))
                before = len(docs)
                _take(src, adapters[src.id], target, since, until, fetcher, raw_dir, seen, docs,
                      stats[src.id])  # fmt: skip
                remaining -= len(docs) - before
    except RequestBudgetExceeded as err:
        stopped = str(err)
        log.warning("stopped early: %s", err)
    manifest = SampleManifest(
        name=name,
        since=since,
        until=until,
        per_country=per_country,
        requests=fetcher.requests,
        stopped_early=stopped,
        stats={sid: {str(k): v for k, v in c.items()} for sid, c in stats.items()},
        documents=docs,
    )
    write_manifest(manifest, samples_dir)
    return manifest
