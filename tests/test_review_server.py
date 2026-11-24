import json
import random
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from review_fixture import DOC1, DOC2, RUN_A, RUN_B, TEXTS, TITLES, build, span
from semval.cli import main
from semval.review.highlights import (
    LOOKALIKES,
    PALETTE_SIZE,
    assign_colors,
    text_pieces,
    value_color,
)
from semval.review.labels import LabelStore, Verdict
from semval.review.server import STATIC_DIR, make_server
from semval.review.session import NOTE_MAX_CHARS, ReviewSession, open_session
from semval.tags import Stance
from semval.values import FRAMEWORK_DIR, load_framework


@contextmanager
def running(session: ReviewSession) -> Iterator[str]:
    server = make_server(session, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def get(url: str, headers: dict | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def post(url: str, body: dict, content_type: str = "application/json") -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": content_type}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def doc_url(base: str, doc_id: str) -> str:
    return f"{base}/api/doc/{urllib.parse.quote(doc_id, safe='')}"


def test_server_serves_items_and_saves(tmp_path: Path) -> None:
    paths = build(tmp_path)
    labels_dir = tmp_path / "labels"
    session = open_session([RUN_A, RUN_B], paths=paths, labels_dir=labels_dir)
    with running(session) as base:
        for path in ("/", "/static/review.js", "/static/review.css"):
            status, _ = get(base + path)
            assert status == 200, path
        assert get(base + "/static/../server.py")[0] == 404

        status, raw = get(base + "/api/items")
        items = json.loads(raw)
        assert status == 200 and items["mode"] == "review"
        assert [d["document_id"] for d in items["documents"]] == [DOC1, DOC2]
        assert [r["run_id"] for r in items["settings"]["runs"]] == [RUN_A, RUN_B]
        assert items["settings"]["runs"][0]["model"] == "claude-haiku-5-5"

        status, raw = get(doc_url(base, DOC1))
        doc = json.loads(raw)
        assert status == 200
        assert "".join(p["t"] for p in doc["pieces"]) == TEXTS[DOC1]
        assert doc["meta"]["title"] == TITLES[DOC1] and doc["meta"]["country"] == "GB"
        assert (doc["index"], doc["total"]) == (1, 2)
        # normal mode: one row per value, the stance of the first run that proposed it
        rows = {r["value_id"]: r for r in doc["rows"]}
        assert rows["alpha"]["stance"] == "endorse" and rows["alpha"]["source_runs"] == [RUN_A]
        assert 0 <= rows["alpha"]["color"] < PALETTE_SIZE
        marked = {m[0] for p in doc["pieces"] for m in p["m"]}
        assert marked == {doc["rows"].index(rows["alpha"]), doc["rows"].index(rows["beta"])}

        status, saved = post(base + "/api/verdict", {
            "document_id": DOC1, "value_id": "alpha", "verdict": "wrong_call",
            "model_stance": "endorse", "corrected_stance": "mention",
        })  # fmt: skip
        assert status == 200
        alpha = next(r for r in saved["rows"] if r["value_id"] == "alpha")
        assert (alpha["verdict"], alpha["verdict_stance"]) == ("wrong_call", "mention")
        status, saved = post(base + "/api/verdict", {
            "document_id": DOC2, "value_id": "alpha", "verdict": "added",
            "corrected_stance": "reject",
        })  # fmt: skip
        assert status == 200
        added = next(r for r in saved["rows"] if r["value_id"] == "alpha")
        assert added["kind"] == "owner" and added["verdict"] == "added"
        assert "alpha" not in {a["value_id"] for a in saved["addable"]}
        assert post(base + "/api/note", {"document_id": DOC2, "note": "hm"})[0] == 200

        # bad input is refused and nothing is stored
        bad = [
            {"document_id": DOC1, "value_id": "alpha", "verdict": "wrong_call",
             "model_stance": "endorse"},  # no corrected stance
            {"document_id": DOC1, "value_id": "alpha", "verdict": "correct",
             "model_stance": "mention"},  # no run proposed that
            {"document_id": DOC1, "value_id": "nope", "verdict": "added",
             "corrected_stance": "endorse"},  # not a target
            {"document_id": "src-gb:missing", "value_id": "alpha", "verdict": "added",
             "corrected_stance": "endorse"},
            {"document_id": DOC1, "value_id": "beta", "verdict": "not_present"},  # proposed:
            # a verdict on it names the stance it judges
            {"document_id": DOC1, "value_id": "beta", "verdict": "added",
             "corrected_stance": "mention"},  # proposed: judge it, do not add it
        ]  # fmt: skip
        for body in bad:
            assert post(base + "/api/verdict", body)[0] == 400, body
        assert get(doc_url(base, "src-gb:missing"))[0] == 404

        doc2 = json.loads(get(doc_url(base, DOC2))[1])
        assert doc2["note"] == "hm"
        beta = next(r for r in doc2["rows"] if r["value_id"] == "beta")
        assert beta["spans"] == 0 and beta["evidence_unresolved"]  # "no quote found"
        assert all(not p["m"] for p in doc2["pieces"])

    got = {
        (r.document_id, r.value_id): r
        for r in LabelStore(labels_dir / "owner" / "labels.jsonl").all()
    }
    assert got[DOC1, "alpha"].source_runs == [RUN_A]
    assert got[DOC1, "alpha"].model_stance == Stance.ENDORSE
    # evidence as offsets: the union over every run that proposed alpha here
    assert got[DOC1, "alpha"].model_evidence == [span(DOC1, "Alpha must be defended")]
    assert got[DOC1, "alpha"].owner_evidence == []
    assert got[DOC2, "alpha"].model_evidence == []
    assert got[DOC2, "alpha"].verdict == Verdict.ADDED and got[DOC2, "alpha"].source_runs == []
    assert len(got) == 2


def test_blind_payload_hides_runs(tmp_path: Path) -> None:
    paths = build(tmp_path)
    labels_dir = tmp_path / "labels"
    store = LabelStore(labels_dir / "owner" / "labels.jsonl")
    pre = open_session([RUN_A, RUN_B], paths=paths, labels_dir=labels_dir)
    pre.save_verdict({"document_id": DOC1, "value_id": "beta", "verdict": "correct",
                      "model_stance": "reject"})  # fmt: skip
    session = open_session([RUN_A, RUN_B], blind=True, paths=paths, labels_dir=labels_dir)
    with running(session) as base:
        bodies = [get(base + "/api/items")[1], get(doc_url(base, DOC1))[1],
                  get(doc_url(base, DOC2))[1]]  # fmt: skip
        status, saved = post(base + "/api/verdict", {
            "document_id": DOC1, "value_id": "alpha", "verdict": "correct",
            "model_stance": "reject",
        })  # fmt: skip
        assert status == 200
        bodies.append(json.dumps(saved).encode())
        items = json.loads(bodies[0])
        assert items["mode"] == "blind" and items.get("settings") is None
        doc1 = json.loads(bodies[1])
        # both proposed stances for alpha; beta was judged before this session
        assert [(r["value_id"], r["stance"]) for r in doc1["rows"]] == [
            ("alpha", "endorse"),
            ("alpha", "reject"),
        ]
        assert "beta" not in {a["value_id"] for a in doc1["addable"]}  # already present
        rows = {r["stance"]: r for r in saved["rows"]}
        # one verdict settles the value: the sibling row shows what it implies
        assert rows["reject"]["verdict"] == "correct"
        assert (rows["endorse"]["verdict"], rows["endorse"]["verdict_stance"]) == (
            "wrong_call",
            "reject",
        )
    for body in bodies:
        text = body.decode()
        for secret in (RUN_A, RUN_B, "claude-", "effort", "source_runs", "run_id"):
            assert secret not in text, secret
    got = {r.value_id: r for r in store.all() if r.document_id == DOC1}
    assert got["alpha"].source_runs == [RUN_B]  # kept server-side, never sent


def test_server_binds_localhost_only(tmp_path: Path) -> None:
    session = open_session([RUN_A], paths=build(tmp_path), labels_dir=tmp_path / "labels")
    server = make_server(session, port=0)
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()
    with running(session) as base:
        # DNS rebinding: a page on another host name must not reach the API
        assert get(base + "/api/items", {"Host": "evil.example"})[0] == 403
        # a cross-site form post cannot send JSON
        body = {"document_id": DOC1, "note": "x"}
        assert post(base + "/api/note", body, content_type="text/plain")[0] == 415


def test_palette_matches_css() -> None:
    css = (STATIC_DIR / "review.css").read_text(encoding="utf-8")
    for i in range(PALETTE_SIZE):
        # light, dark (media query) and dark (explicit theme)
        assert len(re.findall(rf"--hl-{i}:", css)) == 3, i
    assert f"--hl-{PALETTE_SIZE}:" not in css
    assert "background-color" not in re.search(r"\.hl\s*\{[^}]*\}", css).group(0)


def test_cli_review_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("semval.datasets.touche23.DEFAULT_DIR", tmp_path)
    with pytest.raises(SystemExit, match="no candidates yet"):
        main(["review", "--source", "touche23-fewshot"])
    with pytest.raises(SystemExit, match="--run"):
        main(["review"])


def test_missing_text_is_reported_not_fatal(tmp_path: Path) -> None:
    paths = build(tmp_path)
    (paths.raw_dir / "src-gb__000000000001.txt").write_text("changed", encoding="utf-8")
    session = open_session([RUN_A], paths=paths, labels_dir=tmp_path / "labels")
    doc = session.doc_payload(DOC1)
    assert "text_sha256" in doc["text_error"] and doc["pieces"] == []
    assert [r["value_id"] for r in doc["rows"]] == ["alpha", "beta"]


def test_overlapping_quotes_keep_one_lane_each() -> None:
    text = "0123456789"
    pieces = text_pieces(text, {0: [(0, 6)], 1: [(4, 10)], 2: [(7, 9)]})
    assert "".join(p["t"] for p in pieces) == text
    lanes: dict[int, set[int]] = {}
    for p in pieces:
        for row, _span, lane in p["m"]:
            lanes.setdefault(row, set()).add(lane)
    assert lanes == {0: {0}, 1: {1}, 2: {0}}  # 2 reuses lane 0 once 0 has ended
    assert value_color("alpha") == value_color("alpha")


def leaf_ids() -> list[str]:
    fw = load_framework(FRAMEWORK_DIR / "schwartz19.yaml", local_dir=None)
    return fw.target_set("leaf").ids()


def test_article_colours_do_not_collide_on_schwartz19() -> None:
    ids = leaf_ids()
    hashed = [value_color(v) for v in ids]
    assert max(hashed.count(c) for c in hashed) >= 3  # the hash alone collides
    rng = random.Random(1)
    orders = [ids, *(rng.sample(ids, len(ids)) for _ in range(200))]
    for order in orders:
        colors = assign_colors(order)
        assert colors[order[0]] == value_color(order[0])  # the hash stays the first choice
        first12 = [colors[v] for v in order[:12]]
        assert len(set(first12)) == 12  # up to a full palette: all different
        used8 = {colors[v] for v in order[:8]}
        assert not [c for c in used8 if LOOKALIKES.get(c) in used8]  # no look-alike pairs
        counts = [list(colors.values()).count(c) for c in range(PALETTE_SIZE)]
        assert max(counts) <= 2  # 19 values: one wrap-around at most
    magentas = [v for v in ids if value_color(v) == 8]
    assert len(magentas) == 4 and len(set(assign_colors(magentas).values())) == 4


def test_doc_rows_get_article_colours(tmp_path: Path) -> None:
    session = open_session([RUN_A], paths=build(tmp_path), labels_dir=tmp_path / "labels")
    doc = session.doc_payload(DOC1)
    ids = [r["value_id"] for r in doc["rows"]] + [a["value_id"] for a in doc["addable"]]
    colors = assign_colors(ids)
    assert [r["color"] for r in doc["rows"]] == [colors[r["value_id"]] for r in doc["rows"]]
    assert all("color" in a for a in doc["addable"])


def test_note_limits_and_oversized_body(tmp_path: Path) -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert f'maxlength="{NOTE_MAX_CHARS}"' in html
    # the worst case JSON escape (6 bytes a character) still fits the body limit
    assert len(json.dumps({"document_id": DOC1, "note": "" * NOTE_MAX_CHARS})) < 64 * 1024
    session = open_session([RUN_A], paths=build(tmp_path), labels_dir=tmp_path / "labels")
    with running(session) as base:
        too_long = {"document_id": DOC1, "note": "x" * (NOTE_MAX_CHARS + 1)}
        assert post(base + "/api/note", too_long)[0] == 400
        huge = {"document_id": DOC1, "note": "x" * (70 * 1024)}
        status, body = post(base + "/api/note", huge)
        assert status == 413 and "error" in body
        assert get(base + "/api/items")[0] == 200  # still serving
