from pathlib import Path

import pytest
import yaml

from conftest import toy_values, write_framework
from semval.targets import OfficialDefinition, TargetDef, TargetSet
from semval.values import FRAMEWORK_DIR, LEAF_LEVEL, load_framework

SCHWARTZ19 = FRAMEWORK_DIR / "schwartz19.yaml"


def make_target(**overrides) -> dict:
    base = {"id": "first", "name": "First", "definition": "The first target."}
    base.update(overrides)
    return base


def toy_levels() -> list[dict]:
    """Three levels over toy_values(): own targets, reused targets, and projected groups."""
    return [
        {
            "id": "coarse",
            "targets": [make_target(), make_target(id="second", name="Second")],
            "map": {"alpha": "first", "beta": "second"},
        },
        {"id": "coarse_alt", "targets_from": "coarse", "map": {"alpha": "first", "beta": "first"}},
        {
            "id": "sides",
            "value_targets": ["group_a", "group_b"],
            "map": {"alpha": "group_a", "beta": "group_b"},
        },
    ]


def load_toy(tmp_path: Path, levels: list[dict] | None = None, **kwargs):
    levels = toy_levels() if levels is None else levels
    return load_framework(write_framework(tmp_path, toy_values(), levels=levels), **kwargs)


# ---- real framework file ---------------------------------------------------------------


def test_level_map_covers_every_leaf_exactly_once() -> None:
    fw = load_framework(SCHWARTZ19)
    leaf_ids = [v.id for v in fw.leaves()]
    for level_id in fw.level_ids():
        mapping = fw.rollup_map(level_id)
        assert sorted(mapping) == sorted(leaf_ids), level_id
        assert len(mapping) == len(set(leaf_ids)), level_id


def test_level_map_targets_exist() -> None:
    fw = load_framework(SCHWARTZ19)
    for level_id in fw.level_ids():
        targets = set(fw.target_set(level_id).ids())
        assert set(fw.rollup_map(level_id).values()) <= targets, level_id


def test_validation_rollup_humility_to_tradition() -> None:
    fw = load_framework(SCHWARTZ19)
    assert fw.rollup_map("basic10_validation")["humility"] == "tradition"
    assert fw.rollup_map("basic10")["humility"] == "conformity"


def test_targets_from_reuses_targets() -> None:
    fw = load_framework(SCHWARTZ19)
    assert fw.target_set("basic10_validation").targets == fw.target_set("basic10").targets
    assert fw.target_set("basic10_validation").level_id == "basic10_validation"


def test_target_set_leaf_equals_leaves() -> None:
    fw = load_framework(SCHWARTZ19)
    ts = fw.target_set(LEAF_LEVEL)
    assert isinstance(ts, TargetSet)
    assert (ts.framework_id, ts.level_id) == ("schwartz19", LEAF_LEVEL)
    assert ts.ids() == [v.id for v in fw.leaves()]
    for t, v in zip(ts.targets, fw.leaves(), strict=True):
        assert (t.name, t.definition, t.official) == (v.name, v.definition, v.official)
        assert (t.examples_endorse, t.examples_reject) == (v.examples_endorse, v.examples_reject)


# ---- level mechanics on a toy framework ------------------------------------------------


def test_toy_levels(tmp_path: Path) -> None:
    fw = load_toy(tmp_path)
    assert fw.level_ids() == [LEAF_LEVEL, "coarse", "coarse_alt", "sides"]
    assert fw.target_set("coarse").ids() == ["first", "second"]
    assert fw.target_set("coarse_alt").ids() == ["first", "second"]
    assert fw.rollup_map("coarse_alt") == {"alpha": "first", "beta": "first"}
    assert fw.rollup_map(LEAF_LEVEL) == {"alpha": "alpha", "beta": "beta"}


def test_value_targets_project_values(tmp_path: Path) -> None:
    fw = load_toy(tmp_path)
    ts = fw.target_set("sides")
    assert ts.ids() == ["group_a", "group_b"]
    assert ts.targets[0].definition == fw.get("group_a").definition
    assert ts.targets[0].name == "Group A"


def test_target_set_is_a_copy(tmp_path: Path) -> None:
    fw = load_toy(tmp_path)
    fw.target_set(LEAF_LEVEL).targets[0].examples_endorse.append("changed")
    assert fw.get("alpha").examples_endorse == ["Alpha is good."]


def test_unknown_level_raises_key_error(tmp_path: Path) -> None:
    fw = load_toy(tmp_path)
    with pytest.raises(KeyError):
        fw.target_set("nope")
    with pytest.raises(KeyError):
        fw.rollup_map("nope")


def _bad_level(**overrides) -> list[dict]:
    levels = toy_levels()
    levels[0].update(overrides)
    return levels


def _extra_level(target: str = "first", **fields) -> list[dict]:
    return [*toy_levels(), {"id": "x", "map": {"alpha": target, "beta": target}, **fields}]


@pytest.mark.parametrize(
    ("levels", "message"),
    [
        (_bad_level(map={"alpha": "first"}), "beta"),
        (_bad_level(map={"alpha": "first", "beta": "second", "group_a": "first"}), "group_a"),
        (_bad_level(map={"alpha": "first", "beta": "nope"}), "nope"),
        (_bad_level(id=LEAF_LEVEL), "reserved"),
        (_bad_level(id="coarse_alt"), "duplicate level id"),
        (_bad_level(targets_from="sides"), "exactly one"),
        (_bad_level(targets=[]), "exactly one"),
        (_bad_level(targets=[make_target(), make_target()]), "duplicate target id"),
        (_bad_level(id="Bad Id"), "slug"),
        (_extra_level(targets_from="nope"), "unknown level 'nope'"),
        (_extra_level(targets_from="coarse_alt"), "own targets"),
        (_extra_level(targets_from="x"), "own targets"),
        (_extra_level("group_a", value_targets=["nope"]), "unknown value id 'nope'"),
        (_extra_level("alpha", value_targets=["alpha", "alpha"]), "duplicate target id"),
        (_bad_level(extra_field=1), "extra_field"),
    ],
)
def test_bad_levels_rejected(tmp_path: Path, levels: list[dict], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_toy(tmp_path, levels)


# ---- targets.py models -----------------------------------------------------------------


def test_official_definition_needs_text_unless_local() -> None:
    with pytest.raises(ValueError, match="local_only"):
        OfficialDefinition(citation="Someone (2012).", page="p. 1")
    local = OfficialDefinition(citation="Someone (2012).", page="p. 1", local_only=True)
    assert local.text is None
    inline = OfficialDefinition(citation="Someone (2012).", page="p. 1", text="Verbatim.")
    assert not inline.local_only


def test_target_def_validates() -> None:
    assert TargetDef(**make_target()).official is None
    with pytest.raises(ValueError):
        TargetDef(**make_target(id="Not A Slug"))
    with pytest.raises(ValueError):
        TargetDef(**make_target(definition="   "))
    with pytest.raises(ValueError, match="nope"):
        TargetDef(**make_target(nope=1))


def test_target_set_rejects_duplicate_ids() -> None:
    target = TargetDef(**make_target())
    with pytest.raises(ValueError, match="duplicate target id"):
        TargetSet(framework_id="toy", level_id="coarse", targets=[target, target])


# ---- local official texts --------------------------------------------------------------


def _official_local() -> dict:
    return {"citation": "Someone (2012).", "page": "p. 7", "local_only": True}


def _write_local(local_dir: Path, doc: dict, fid: str = "toy") -> None:
    local_dir.mkdir(exist_ok=True)
    text = yaml.safe_dump(doc)
    (local_dir / f"{fid}.official.yaml").write_text(text, encoding="utf-8")


def _official_toy(tmp_path: Path) -> Path:
    values = toy_values()
    values[2]["official"] = _official_local()
    levels = toy_levels()
    levels[0]["targets"][0]["official"] = _official_local()
    return write_framework(tmp_path, values, levels=levels)


def test_local_official_text_merged(tmp_path: Path) -> None:
    path = _official_toy(tmp_path)
    local_dir = tmp_path / "local"
    doc = {"values": {"alpha": "Alpha, verbatim."}, "levels": {"coarse": {"first": "First."}}}
    _write_local(local_dir, doc)
    fw = load_framework(path, local_dir=local_dir)
    assert fw.target_set(LEAF_LEVEL).targets[0].official.text == "Alpha, verbatim."
    assert fw.target_set("coarse").targets[0].official.text == "First."
    assert fw.target_set("coarse_alt").targets[0].official.text == "First."
    assert fw.target_set("coarse").targets[0].official.citation == "Someone (2012)."


def test_local_official_absent_leaves_text_none(tmp_path: Path) -> None:
    fw = load_framework(_official_toy(tmp_path), local_dir=tmp_path / "missing")
    assert fw.get("alpha").official.text is None
    assert load_framework(_official_toy(tmp_path), local_dir=None).get("alpha").official


@pytest.mark.parametrize(
    ("doc", "message"),
    [
        ({"values": {"nope": "x."}}, "nope"),
        ({"values": {"beta": "x."}}, "beta"),
        ({"levels": {"nope": {"first": "x."}}}, "nope"),
        ({"levels": {"coarse": {"second": "x."}}}, "second"),
        ({"levels": {"coarse_alt": {"first": "x."}}}, "coarse_alt"),
        ({"other": {}}, "other"),
    ],
)
def test_bad_local_official_rejected(tmp_path: Path, doc: dict, message: str) -> None:
    path = _official_toy(tmp_path)
    _write_local(tmp_path / "local", doc)
    with pytest.raises(ValueError, match=message):
        load_framework(path, local_dir=tmp_path / "local")


def test_local_text_not_merged_over_inline_text(tmp_path: Path) -> None:
    values = toy_values()
    values[2]["official"] = {"citation": "Someone (2012).", "page": "p. 7", "text": "Inline."}
    path = write_framework(tmp_path, values, levels=toy_levels())
    _write_local(tmp_path / "local", {"values": {"alpha": "Local."}})
    with pytest.raises(ValueError, match="local_only"):
        load_framework(path, local_dir=tmp_path / "local")
