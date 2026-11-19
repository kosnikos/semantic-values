import datetime
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from review_fixture import DOC1, DOC2, RUN_A, RUN_B, TEXTS, build
from semval.review.labels import LabelRecord, LabelStore, NoteStore, Verdict
from semval.review.pool import pool_unjudged
from semval.review.session import open_session
from semval.tagging.runfiles import load_run
from semval.tags import Stance

NOW = datetime.datetime(2026, 11, 19, 12, 0, tzinfo=datetime.UTC)


def rec(**kw) -> LabelRecord:
    base = {
        "labeller": "owner", "document_id": DOC1, "value_id": "alpha", "level_id": "leaf",
        "model_stance": Stance.ENDORSE, "verdict": Verdict.CORRECT, "source_runs": [RUN_A],
        "updated": NOW,
    }  # fmt: skip
    base.update(kw)
    return LabelRecord(**base)


def test_verdict_upsert_last_write_wins(tmp_path: Path) -> None:
    path = tmp_path / "owner" / "labels.jsonl"
    store = LabelStore(path)
    store.upsert(rec())
    store.upsert(rec(verdict=Verdict.NOT_PRESENT))  # a re-click
    store.upsert(rec(verdict=Verdict.WRONG_CALL, corrected_stance=Stance.REJECT))
    store.upsert(rec(value_id="beta"))
    store.upsert(rec(level_id="basic10"))  # another level is another key
    got = {(r.value_id, r.level_id): r for r in LabelStore(path).all()}  # a reload
    assert set(got) == {("alpha", "leaf"), ("beta", "leaf"), ("alpha", "basic10")}
    assert got["alpha", "leaf"].verdict == Verdict.WRONG_CALL
    assert got["alpha", "leaf"].corrected_stance == Stance.REJECT
    # append-only: every write is kept
    assert len(path.read_text(encoding="utf-8").splitlines()) == 5


def test_store_survives_a_torn_last_line(tmp_path: Path) -> None:
    path = tmp_path / "labels.jsonl"
    store = LabelStore(path)
    store.upsert(rec())
    with path.open("a", encoding="utf-8") as f:
        f.write('{"labeller": "owner", "docum')  # a crash mid-write
    assert len(store.all()) == 1
    store.upsert(rec(value_id="beta"))
    assert {r.value_id for r in store.all()} == {"alpha", "beta"}


def test_wrong_call_requires_corrected_stance() -> None:
    with pytest.raises(ValidationError, match="corrected_stance"):
        rec(verdict=Verdict.WRONG_CALL)
    with pytest.raises(ValidationError, match="corrected_stance"):
        rec(verdict=Verdict.ADDED, model_stance=None)
    with pytest.raises(ValidationError, match="differ"):
        rec(verdict=Verdict.WRONG_CALL, corrected_stance=Stance.ENDORSE)
    with pytest.raises(ValidationError, match="model_stance"):
        rec(verdict=Verdict.ADDED, corrected_stance=Stance.REJECT)
    with pytest.raises(ValidationError, match="model_stance"):
        rec(verdict=Verdict.CORRECT, model_stance=None)
    with pytest.raises(ValidationError, match="corrected_stance"):
        rec(verdict=Verdict.CORRECT, corrected_stance=Stance.REJECT)
    with pytest.raises(ValidationError, match="contested"):
        rec(verdict=Verdict.WRONG_CALL, corrected_stance=Stance.CONTESTED)
    # a NOT_PRESENT without a model stance withdraws a value the owner added
    assert rec(verdict=Verdict.NOT_PRESENT, model_stance=None).present_stance() is None
    assert rec(verdict=Verdict.ADDED, model_stance=None, corrected_stance=Stance.MENTION)
    assert rec().present_stance() == Stance.ENDORSE


def test_label_file_has_no_text(tmp_path: Path) -> None:
    paths = build(tmp_path)
    labels_dir = tmp_path / "labels"
    session = open_session([RUN_A, RUN_B], paths=paths, labels_dir=labels_dir)
    session.save_verdict({"document_id": DOC1, "value_id": "alpha", "verdict": "correct",
                          "model_stance": "endorse"})  # fmt: skip
    session.save_verdict({"document_id": DOC1, "value_id": "beta", "verdict": "wrong_call",
                          "model_stance": "reject", "corrected_stance": "mention"})  # fmt: skip
    session.save_verdict({"document_id": DOC2, "value_id": "alpha", "verdict": "added",
                          "corrected_stance": "endorse"})  # fmt: skip
    session.save_note({"document_id": DOC2, "note": "owner remark"})
    files = sorted((labels_dir / "owner").glob("*.jsonl"))
    assert [f.name for f in files] == ["labels.jsonl", "notes.jsonl"]
    words = {w.strip(".,") for t in TEXTS.values() for w in t.split() if len(w) > 4}
    for f in files:
        content = f.read_text(encoding="utf-8")
        assert not [w for w in words if w in content]
    lines = (labels_dir / "owner" / "labels.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    for line in lines:
        assert set(json.loads(line)) == set(LabelRecord.model_fields)


def test_pool_unjudged_excludes_judged_and_hides_run(tmp_path: Path) -> None:
    paths = build(tmp_path)
    runs = [load_run(paths.runs_dir, r) for r in (RUN_A, RUN_B)]
    store = LabelStore(tmp_path / "labels" / "owner" / "labels.jsonl")

    items = pool_unjudged(runs, store, "owner", runs_dir=paths.runs_dir)
    pairs = [(i.document_id, i.value_id, i.stance) for i in items]
    # every distinct proposed (value, stance), in an order that does not follow the runs
    assert pairs == [
        (DOC1, "alpha", Stance.ENDORSE),
        (DOC1, "alpha", Stance.REJECT),
        (DOC1, "beta", Stance.REJECT),
        (DOC2, "beta", Stance.MENTION),
    ]
    unresolved = items[-1]
    assert unresolved.evidence == [] and unresolved.evidence_unresolved

    store.upsert(rec(verdict=Verdict.WRONG_CALL, corrected_stance=Stance.MENTION))
    store.upsert(rec(labeller="someone_else", value_id="beta"))  # not this labeller's
    store.upsert(rec(value_id="beta", level_id="basic10"))  # not this level
    items = pool_unjudged(runs, store, "owner", runs_dir=paths.runs_dir)
    assert [(i.document_id, i.value_id) for i in items] == [(DOC1, "beta"), (DOC2, "beta")]

    dumped = json.dumps([i.model_dump(mode="json") for i in items])
    for secret in (RUN_A, RUN_B, "haiku", "sonnet", "effort", "run"):
        assert secret not in dumped


def test_pool_rejects_runs_at_different_levels(tmp_path: Path) -> None:
    paths = build(tmp_path)
    a = load_run(paths.runs_dir, RUN_A)
    b = load_run(paths.runs_dir, RUN_B)
    b.spec = b.spec.model_copy(update={"level_id": "basic10"})
    store = LabelStore(tmp_path / "labels.jsonl")
    with pytest.raises(ValueError, match="framework and level"):
        pool_unjudged([a, b], store, "owner", runs_dir=paths.runs_dir)


def test_note_store_last_write_wins(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "notes.jsonl")
    store.set("owner", DOC1, "first")
    store.set("owner", DOC1, "second")
    store.set("owner", DOC2, "other")
    assert store.get("owner", DOC1) == "second"
    assert store.get("owner", "missing") == ""
