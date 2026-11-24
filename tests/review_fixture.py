"""A two-article, two-run fixture for the review page tests. Texts live in a tmp raw dir."""

import hashlib
import json
from datetime import date
from pathlib import Path

from conftest import toy_values, write_framework
from semval.config import HAIKU_5_5, SONNET_5_5, Effort
from semval.sampling.sample import SampleManifest, doc_meta_path, doc_text_path, write_manifest
from semval.tagging.base import RunManifest, RunStatus, TaggerKind, TaggerSpec
from semval.tagging.runfiles import MANIFEST, TAGS, RunPaths
from semval.tags import EvidenceSpan, Stance, ValueTag
from semval.units import Document, UnitLevel

DOC1 = "src-gb:000000000001"
DOC2 = "src-gr:000000000002"
TEXTS = {
    DOC1: "Alpha must be defended. Beta is overrated, says the author.",
    DOC2: "Κείμενο χωρίς αξίες.\n\nBeta matters here, somewhat.",
}
TITLES = {DOC1: "A title about alpha", DOC2: "Ένας τίτλος"}
RUN_A, RUN_B = "run-a", "run-b"


def span(doc_id: str, quote: str) -> EvidenceSpan:
    start = TEXTS[doc_id].index(quote)
    return EvidenceSpan(start=start, end=start + len(quote))


def _write_run(paths: RunPaths, run_id: str, model: str, effort: Effort, tags: list[ValueTag],
               level_id: str = "leaf") -> None:  # fmt: skip
    spec = TaggerSpec(
        kind=TaggerKind.CLAUDE, model=model, effort=effort, framework_id="toy",
        level_id=level_id, unit=UnitLevel.ARTICLE,
    )  # fmt: skip
    m = RunManifest(
        run_id=run_id, spec=spec, input_sample="toy-sample", prompt_sha256="0" * 64,
        status=RunStatus.DONE, segments_done=[f"{DOC1}:a", f"{DOC2}:a"],
    )  # fmt: skip
    run_dir = Path(paths.runs_dir) / run_id
    run_dir.mkdir(parents=True)
    (run_dir / MANIFEST).write_text(m.model_dump_json(indent=2), encoding="utf-8")
    (run_dir / TAGS).write_text("".join(t.model_dump_json() + "\n" for t in tags), "utf-8")


def tag(doc_id: str, value_id: str, stance: Stance, run_id: str, *quotes: str) -> ValueTag:
    return ValueTag(
        segment_id=f"{doc_id}:a", value_id=value_id, stance=stance,
        evidence=[span(doc_id, q) for q in quotes], evidence_unresolved=not quotes,
        run_id=run_id,
    )  # fmt: skip


def build(tmp_path: Path) -> RunPaths:
    """Framework ``toy`` (leaves alpha, beta), sample ``toy-sample`` and runs ``run-a``
    (Haiku: doc1 alpha endorse, doc1 beta reject) and ``run-b`` (Sonnet: doc1 alpha reject,
    doc2 beta mention with no quote found)."""
    paths = RunPaths(
        samples_dir=tmp_path / "samples", raw_dir=tmp_path / "raw",
        framework_dir=tmp_path / "fw", runs_dir=tmp_path / "runs",
    )  # fmt: skip
    paths.framework_dir.mkdir()
    write_framework(paths.framework_dir, toy_values())
    docs = []
    for doc_id, text in TEXTS.items():
        data = text.encode("utf-8")
        p = doc_text_path(paths.raw_dir, doc_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        meta = {"id": doc_id, "url": f"https://example.org/{doc_id}", "title": TITLES[doc_id]}
        doc_meta_path(paths.raw_dir, doc_id).write_text(json.dumps(meta), encoding="utf-8")
        gr = doc_id.startswith("src-gr")
        docs.append(
            Document(
                id=doc_id, source_id=doc_id.split(":")[0], country="GR" if gr else "GB",
                language="el" if gr else "en", genre="opinion", date=date(2026, 3, 1),
                url=f"https://example.org/{doc_id}", title_sha256="1" * 64,
                text_sha256=hashlib.sha256(data).hexdigest(),
            )
        )  # fmt: skip
    write_manifest(
        SampleManifest(
            name="toy-sample", since=date(2026, 1, 1), until=date(2026, 6, 1), per_country=1,
            requests=0, stats={}, documents=docs,
        ),
        paths.samples_dir,
    )  # fmt: skip
    _write_run(paths, RUN_A, HAIKU_5_5, Effort.LOW, [
        tag(DOC1, "alpha", Stance.ENDORSE, RUN_A, "Alpha must be defended"),
        tag(DOC1, "beta", Stance.REJECT, RUN_A, "Beta is overrated"),
    ])  # fmt: skip
    _write_run(paths, RUN_B, SONNET_5_5, Effort.MEDIUM, [
        tag(DOC1, "alpha", Stance.REJECT, RUN_B, "Alpha must be defended"),
        tag(DOC2, "beta", Stance.MENTION, RUN_B),
    ])  # fmt: skip
    return paths
