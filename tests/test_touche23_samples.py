import hashlib
from pathlib import Path

import yaml

from semval.datasets import touche23 as t
from semval.datasets import touche23_samples as ts
from semval.sampling.sample import doc_text_path
from semval.tagging.runfiles import load_sample, read_text
from semval.units import UnitLevel, segment
from semval.values import FRAMEWORK_DIR, load_framework

FW = load_framework(FRAMEWORK_DIR / "schwartz19.yaml", local_dir=None)
N_ITEMS = 40
PROXY_IDS = ["T07", "T21", "T33"]


def _make_data(tmp_path: Path) -> Path:
    d = tmp_path / "ext"
    d.mkdir()
    cats = list(t.TOUCHE23_CATEGORIES)
    arg = ["Argument ID\tConclusion\tStance\tPremise"]
    lab = ["Argument ID\t" + "\t".join(cats)]
    for i in range(N_ITEMS):
        iid = f"T{i:02d}"
        arg.append(f"{iid}\tConc {i}\tagainst\tPremise {i}.")
        flags = ["0"] * len(cats)
        flags[i % 19] = "1"
        lab.append(iid + "\t" + "\t".join(flags))
    (d / "arguments-test.tsv").write_text("\n".join(arg) + "\n", encoding="utf-8")
    (d / "labels-test.tsv").write_text("\n".join(lab) + "\n", encoding="utf-8")
    english = {i.id: i for i in t.load_split("test", d)}
    greek = [
        english[i].model_copy(
            update={"conclusion": f"Συμπέρασμα {i}", "premise": "Μια πρόταση.", "language": "el"}
        )
        for i in PROXY_IDS
    ]
    (d / t.PROXY_FILE).write_text(
        "".join(g.model_dump_json() + "\n" for g in greek), encoding="utf-8"
    )
    return d


def _make(tmp_path: Path, name: str, **kw):  # type: ignore[no-untyped-def]
    d = _make_data(tmp_path) if not (tmp_path / "ext").exists() else tmp_path / "ext"
    path = ts.make_touche_sample(
        name, data_dir=d, samples_dir=tmp_path / "samples", raw_dir=tmp_path / "raw", **kw
    )
    return path, d


def _ids(path: Path) -> list[str]:
    return [x["id"] for x in yaml.safe_load(path.read_text(encoding="utf-8"))["documents"]]


def test_english_sample_contains_all_proxy_ids(tmp_path: Path) -> None:
    path, _ = _make(tmp_path, "en", n=10, seed=3)
    ids = _ids(path)
    assert len(ids) == 10 and len(set(ids)) == 10
    for i in PROXY_IDS:
        assert f"{ts.EN_PREFIX}:{i}" in ids


def test_sample_deterministic_for_seed(tmp_path: Path) -> None:
    a, _ = _make(tmp_path, "a", n=10, seed=5)
    b, _ = _make(tmp_path, "b", n=10, seed=5)
    c, _ = _make(tmp_path, "c", n=10, seed=6)
    assert _ids(a) == _ids(b)
    assert _ids(a) != _ids(c)


def test_proxy_sample_uses_greek_text_and_same_item_ids(tmp_path: Path) -> None:
    _make(tmp_path, "el", proxy=True)
    sample = load_sample("el", tmp_path / "samples")
    assert [d.id for d in sample.documents] == [f"{ts.EL_PREFIX}:{i}" for i in PROXY_IDS]
    assert all(d.language == "el" for d in sample.documents)
    assert "Συμπέρασμα T07" in read_text(tmp_path / "raw", sample.documents[0])


def test_document_text_matches_rendering_and_hash(tmp_path: Path) -> None:
    _make(tmp_path, "en", n=5)
    sample = load_sample("en", tmp_path / "samples")
    items = {i.id: i for i in t.load_split("test", tmp_path / "ext")}
    for doc in sample.documents:
        item = items[doc.id.split(":", 1)[1]]
        data = doc_text_path(tmp_path / "raw", doc.id).read_bytes()
        assert data.decode("utf-8") == item.text
        assert doc.text_sha256 == hashlib.sha256(data).hexdigest()
        assert (doc.source_id, doc.country, doc.genre, doc.language) == (
            ts.EN_PREFIX,
            ts.NO_COUNTRY,
            ts.GENRE,
            "en",
        )
        assert doc.date is None and doc.title is None and doc.url == ts.ZENODO_URL


def test_runner_reads_touche_sample(tmp_path: Path) -> None:
    _make(tmp_path, "en", n=5)
    sample = load_sample("en", tmp_path / "samples")
    doc = sample.documents[0]
    text = read_text(tmp_path / "raw", doc)
    segs = segment(doc.id, text, UnitLevel.PARAGRAPH)
    assert [x.level for x in segs] == [
        UnitLevel.ARTICLE,
        UnitLevel.PARAGRAPH,
    ]


def test_touche_gold_at_basic10_rolls_up_and_objectivity(tmp_path: Path) -> None:
    d = _make_data(tmp_path)
    lines = (d / "labels-test.tsv").read_text(encoding="utf-8").splitlines()
    row = lines[1].split("\t")
    row[1:] = ["0"] * (len(row) - 2) + ["1"]  # T00: objectivity only
    lines[1] = "\t".join(row)
    (d / "labels-test.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _make(tmp_path, "en", n=N_ITEMS)
    sample = load_sample("en", tmp_path / "samples")
    gold = ts.touche_gold(sample, FW, "basic10", data_dir=d)
    assert set(gold) == {x.id for x in sample.documents}
    assert gold[f"{ts.EN_PREFIX}:T00"] == {"universalism"}
    assert gold[f"{ts.EN_PREFIX}:T04"] == {FW.rollup_map("basic10")["achievement"]}
    # proxy documents carry the same gold as their English twin
    _make(tmp_path, "el", proxy=True)
    pg = ts.touche_gold(load_sample("el", tmp_path / "samples"), FW, "basic10", data_dir=d)
    assert pg[f"{ts.EL_PREFIX}:T07"] == gold[f"{ts.EN_PREFIX}:T07"]
