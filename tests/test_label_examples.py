import hashlib
import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from conftest import toy_values, write_framework
from semval.cli import build_parser, main
from semval.config import Effort, ModelId
from semval.review.labels import LabelRecord, LabelStore, Verdict, label_paths
from semval.sampling.sample import SampleManifest, doc_text_path, write_manifest
from semval.tagging.base import RawTag, RunManifest, RunStatus, TaggerKind, TaggerSpec
from semval.tagging.fewshot import load_fewshot, load_fewshot_files, write_fewshot
from semval.tagging.label_examples import (
    excluded_documents,
    select_label_examples,
    write_local_fewshot,
)
from semval.tagging.prompt import FewShotExample
from semval.tagging.runfiles import MANIFEST, TAGS, RunPaths
from semval.tags import EvidenceSpan, Stance, ValueTag
from semval.units import Document, UnitLevel

RUN = "src-run"
SHORT = "Short opening."


def para(i: int) -> str:
    return f"Paragraph {i} " + ("word " * 50) + "KEY PHRASE here " + ("tail " * 10).rstrip()


class Env:
    def __init__(self, tmp_path: Path) -> None:
        self.paths = RunPaths(
            samples_dir=tmp_path / "samples", raw_dir=tmp_path / "raw",
            framework_dir=tmp_path / "fw", runs_dir=tmp_path / "runs",
        )  # fmt: skip
        self.labels = tmp_path / "labels"
        self.docs: list[Document] = []
        self.texts: dict[str, str] = {}
        self.tags: list[ValueTag] = []
        self.records: list[LabelRecord] = []
        self.paths.framework_dir.mkdir()
        write_framework(self.paths.framework_dir, toy_values())

    def doc(self, doc_id: str, lang: str, n: int = 4, short_first: bool = False) -> str:
        paras = [para(i) for i in range(n)]
        if short_first:
            paras[0] = SHORT
        text = "\n\n".join(paras)
        self.texts[doc_id] = text
        data = text.encode("utf-8")
        p = doc_text_path(self.paths.raw_dir, doc_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        self.docs.append(
            Document(
                id=doc_id, source_id=doc_id.split(":")[0], country="GR" if lang == "el" else "GB",
                language=lang, genre="opinion", date=date(2026, 3, 1),
                text_sha256=hashlib.sha256(data).hexdigest(),
            )
        )  # fmt: skip
        return doc_id

    def tag(self, doc_id: str, p: int, value: str, stance: Stance, *, owner=..., unresolved=False,
            quote: str = "KEY PHRASE") -> None:  # fmt: skip
        """Add a paragraph tag; ``owner`` is the owner's stance (default: confirms; None: no label)."""
        text = self.texts[doc_id]
        start_p = text.index(para(p)) if para(p) in text else 0
        s = text.index(quote, start_p) if quote in text[start_p:] else 0
        ev = [] if unresolved else [EvidenceSpan(start=s, end=s + len(quote))]
        self.tags.append(
            ValueTag(segment_id=f"{doc_id}:p{p}", value_id=value, stance=stance,
                     evidence=ev, evidence_unresolved=unresolved, run_id=RUN)
        )  # fmt: skip
        if owner is ...:
            owner = stance
        if owner is not None and not any(
            r.document_id == doc_id and r.value_id == value for r in self.records
        ):
            kw: dict = {"verdict": Verdict.CORRECT}
            if owner != stance:
                kw = {"verdict": Verdict.WRONG_CALL, "corrected_stance": owner}
            self.records.append(
                LabelRecord(labeller="owner", document_id=doc_id, value_id=value,
                            level_id="leaf", model_stance=stance, **kw)
            )  # fmt: skip

    def build(self) -> "Env":
        spec = TaggerSpec(
            kind=TaggerKind.CLAUDE, model=ModelId.SONNET_5_5, effort=Effort.MEDIUM,
            framework_id="toy", level_id="leaf", unit=UnitLevel.PARAGRAPH,
        )  # fmt: skip
        m = RunManifest(run_id=RUN, spec=spec, input_sample="toy-sample",
                        prompt_sha256="0" * 64, status=RunStatus.DONE)  # fmt: skip
        d = self.paths.runs_dir / RUN
        d.mkdir(parents=True)
        (d / MANIFEST).write_text(m.model_dump_json(), encoding="utf-8")
        (d / TAGS).write_text("".join(t.model_dump_json() + "\n" for t in self.tags), "utf-8")
        write_manifest(
            SampleManifest(name="toy-sample", since=date(2026, 1, 1), until=date(2026, 12, 1),
                           per_country=1, requests=0, stats={}, documents=self.docs),
            self.paths.samples_dir,
        )  # fmt: skip
        store = LabelStore(label_paths(self.labels, "owner")[0])
        for r in self.records:
            store.upsert(r)
        return self

    def select(self, n: int = 6) -> list[FewShotExample]:
        return select_label_examples(RUN, "owner", n, paths=self.paths, labels_dir=self.labels)


def test_confirmed_paragraph_selected(tmp_path: Path) -> None:
    e = Env(tmp_path)
    e.tag(e.doc("gr:1", "el"), 0, "alpha", Stance.REJECT)
    (ex,) = e.build().select()
    assert ex.id == "gr:1:p0"
    assert ex.language == "el"
    assert ex.text == para(0)
    assert ex.tags == [RawTag(value_id="alpha", stance="reject", quotes=["KEY PHRASE"])]
    assert "owner-confirmed" in ex.source and "local" in ex.source


def test_endorse_only_paragraph_not_candidate(tmp_path: Path) -> None:
    e = Env(tmp_path)
    e.tag(e.doc("gr:1", "el"), 0, "alpha", Stance.ENDORSE)
    assert e.build().select() == []


def test_unconfirmed_tag_disqualifies_whole_paragraph(tmp_path: Path) -> None:
    e = Env(tmp_path)
    d = e.doc("gr:1", "el")
    e.tag(d, 0, "alpha", Stance.REJECT)
    e.tag(d, 0, "beta", Stance.MENTION, owner=None)  # no owner label
    assert e.build().select() == []


def test_mismatched_stance_disqualifies(tmp_path: Path) -> None:
    e = Env(tmp_path)
    e.tag(e.doc("gr:1", "el"), 0, "alpha", Stance.REJECT, owner=Stance.ENDORSE)
    assert e.build().select() == []


def test_not_present_disqualifies(tmp_path: Path) -> None:
    e = Env(tmp_path)
    d = e.doc("gr:1", "el")
    e.tag(d, 0, "alpha", Stance.REJECT, owner=None)
    e.records.append(
        LabelRecord(labeller="owner", document_id=d, value_id="alpha", level_id="leaf",
                    model_stance=Stance.REJECT, verdict=Verdict.NOT_PRESENT)
    )  # fmt: skip
    assert e.build().select() == []


def test_unresolved_evidence_disqualifies(tmp_path: Path) -> None:
    e = Env(tmp_path)
    d = e.doc("gr:1", "el")
    e.tag(d, 0, "alpha", Stance.REJECT, unresolved=True)
    e.tag(d, 1, "alpha", Stance.REJECT)
    assert [x.id for x in e.build().select()] == ["gr:1:p1"]


def test_short_paragraph_disqualifies(tmp_path: Path) -> None:
    e = Env(tmp_path)
    d = e.doc("gr:1", "el", short_first=True)
    e.tag(d, 0, "alpha", Stance.REJECT, quote="Short")
    e.tag(d, 1, "alpha", Stance.REJECT)
    assert [x.id for x in e.build().select()] == ["gr:1:p1"]


def test_quotes_clipped_and_substrings(tmp_path: Path) -> None:
    e = Env(tmp_path)
    d = e.doc("en:1", "en")
    e.tag(d, 0, "alpha", Stance.REJECT)
    e.tag(d, 0, "alpha", Stance.REJECT)  # same value and stance collapses to one RawTag
    p0_end = e.texts[d].index(para(0)) + len(para(0))
    # evidence running past the paragraph end is clipped to it
    e.tags[-1] = e.tags[-1].model_copy(
        update={"evidence": [EvidenceSpan(start=p0_end - 4, end=p0_end + 20)]}
    )
    (ex,) = e.build().select()
    assert len(ex.tags) == 1
    assert len(ex.tags[0].quotes) == 2
    assert all(q in ex.text for q in ex.tags[0].quotes)


def test_cap_two_per_article(tmp_path: Path) -> None:
    e = Env(tmp_path)
    d = e.doc("gr:1", "el", 5)
    for p in range(4):
        e.tag(d, p, "alpha", Stance.REJECT)
    got = e.build().select(6)
    assert [x.id for x in got] == ["gr:1:p0", "gr:1:p1"]


def test_alternates_languages_and_is_deterministic(tmp_path: Path) -> None:
    e = Env(tmp_path)
    for i in range(3):
        e.tag(e.doc(f"gr:{i}", "el"), 0, "alpha", Stance.REJECT)
        e.tag(e.doc(f"en:{i}", "en"), 0, "beta", Stance.MENTION)
    e.build()
    a, b = e.select(4), e.select(4)
    assert a == b
    assert [x.language for x in a] == ["el", "en", "el", "en"]


def test_covers_both_stances_first(tmp_path: Path) -> None:
    e = Env(tmp_path)
    for i in range(3):
        e.tag(e.doc(f"gr:{i}", "el"), 0, "alpha", Stance.REJECT)
    e.tag(e.doc("gr:9", "el"), 0, "beta", Stance.MENTION)
    got = e.build().select(2)
    assert {t.stance for x in got for t in x.tags} == {"reject", "mention"}


def test_excluded_documents_and_header(tmp_path: Path) -> None:
    e = Env(tmp_path)
    e.tag(e.doc("gr:1", "el"), 0, "alpha", Stance.REJECT)
    e.tag(e.doc("en:1", "en"), 1, "beta", Stance.MENTION)
    ex = e.build().select()
    out = tmp_path / "local" / "articles.yaml"
    write_local_fewshot(out, ex, run_id=RUN, labeller="owner")
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["source_documents"] == ["en:1", "gr:1"]
    assert data["source_run"] == RUN and data["labeller"] == "owner"
    assert "not for commit" in data["notice"].lower()
    assert load_fewshot(out) == ex
    touche = tmp_path / "t.yaml"
    write_fewshot(touche, ex)
    assert excluded_documents([out, touche]) == {"gr:1", "en:1"}
    assert excluded_documents([touche]) == set()
    assert excluded_documents([]) == set()


def test_load_fewshot_files_concatenates_in_order(tmp_path: Path) -> None:
    def ex(i: str) -> FewShotExample:
        return FewShotExample(id=i, text="t", language="en", tags=[], source="s")

    a, b = tmp_path / "a.yaml", tmp_path / "b.yaml"
    write_fewshot(a, [ex("a1"), ex("a2")])
    write_fewshot(b, [ex("b1")])
    assert [x.id for x in load_fewshot_files([b, a])] == ["b1", "a1", "a2"]


def test_few_shot_file_flag_repeatable() -> None:
    base = ["tag", "--sample", "s", "--model", "claude-sonnet-5-5", "--effort", "medium",
            "--level", "leaf", "--unit", "paragraph"]  # fmt: skip
    p = build_parser()
    args = p.parse_args([*base, "--few-shot-file", "x.yaml", "--few-shot-file", "y.yaml"])
    assert args.few_shot_file == [Path("x.yaml"), Path("y.yaml")]
    assert p.parse_args(base).few_shot_file is None


def test_manifest_without_few_shot_files_loads() -> None:
    old = {
        "run_id": "r", "spec": {"kind": "lexicon", "framework_id": "f", "level_id": "leaf"},
        "input_sample": "s", "prompt_sha256": "0" * 64, "status": "done",
    }  # fmt: skip
    assert RunManifest.model_validate_json(json.dumps(old)).few_shot_files == []


def test_cli_from_labels(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    e = Env(tmp_path)
    e.tag(e.doc("gr:1", "el"), 0, "alpha", Stance.REJECT)
    e.build()
    out = tmp_path / "local" / "articles.yaml"
    rc = main(["fewshot", "from-labels", "--run", RUN, "--labels-dir", str(e.labels),
               "--out", str(out), "--runs-dir", str(e.paths.runs_dir),
               "--samples-dir", str(e.paths.samples_dir), "--raw-dir", str(e.paths.raw_dir)])  # fmt: skip
    assert rc == 0 and out.exists()
    printed = capsys.readouterr().out
    assert "el" in printed and "reject" in printed and "gr:1" in printed
