from pathlib import Path

import pytest

from conftest import make_value, toy_values, write_framework
from semval.values import FRAMEWORK_DIR, LEAF_LEVEL, Framework, ValueDef, load_framework

FRAMEWORK_FILES = sorted(FRAMEWORK_DIR.glob("*.yaml"))


def test_framework_files_exist() -> None:
    assert FRAMEWORK_FILES, f"no framework files in {FRAMEWORK_DIR}"


@pytest.mark.parametrize("path", FRAMEWORK_FILES, ids=lambda p: p.name)
def test_values_yaml_loads(path: Path) -> None:
    fw = load_framework(path)
    assert fw.id == path.stem
    assert len(fw.values) >= 10
    for v in fw.values:
        assert v.definition.strip(), v.id
        assert v.framework == fw.id


@pytest.mark.parametrize("path", FRAMEWORK_FILES, ids=lambda p: p.name)
def test_taggable_values_have_stance_examples(path: Path) -> None:
    fw = load_framework(path)
    assert len(fw.leaves()) >= 10
    for v in fw.leaves():
        assert v.examples_endorse, f"{v.id}: no examples_endorse"
        assert v.examples_reject, f"{v.id}: no examples_reject"


def test_duplicate_value_ids_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, [make_value(), make_value(name="Alpha again")])
    with pytest.raises(ValueError, match="duplicate value id: alpha"):
        load_framework(path)


def test_unknown_reference_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, [make_value(opposes=["nope"])])
    with pytest.raises(ValueError, match="nope"):
        load_framework(path)


def test_unknown_parent_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, [make_value(parent="missing_group")])
    with pytest.raises(ValueError, match="missing_group"):
        load_framework(path)


def test_self_reference_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, [make_value(opposes=["alpha"])])
    with pytest.raises(ValueError, match="alpha.*itself"):
        load_framework(path)


def test_asymmetric_opposes_rejected(tmp_path: Path) -> None:
    values = toy_values()
    values[3]["opposes"] = []
    path = write_framework(tmp_path, values)
    with pytest.raises(ValueError, match="beta"):
        load_framework(path)


def test_parent_cycle_rejected(tmp_path: Path) -> None:
    values = [make_value(id="a", parent="b"), make_value(id="b", parent="a")]
    path = write_framework(tmp_path, values)
    with pytest.raises(ValueError, match="cycle"):
        load_framework(path)


def test_framework_field_mismatch_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, [make_value(framework="other")])
    with pytest.raises(ValueError, match="other"):
        load_framework(path)


@pytest.mark.parametrize("bad", ["Alpha", "has space", "1abc", "dash-ed", ""])
def test_bad_slug_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        ValueDef(**make_value(id=bad), framework="toy")


def test_empty_definition_rejected() -> None:
    with pytest.raises(ValueError):
        ValueDef(**make_value(definition="   "), framework="toy")


def test_unknown_field_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, [make_value(oppose=["beta"])])
    with pytest.raises(ValueError, match="oppose"):
        load_framework(path)


def test_groups_and_leaves(tmp_path: Path) -> None:
    fw = load_framework(write_framework(tmp_path, toy_values()))
    assert [v.id for v in fw.groups()] == ["group_a", "group_b"]
    assert [v.id for v in fw.leaves()] == ["alpha", "beta"]
    assert fw.get("beta").parent == "group_b"
    with pytest.raises(KeyError):
        fw.get("nope")


def test_two_frameworks_coexist(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    fw_a = load_framework(write_framework(tmp_path / "a", toy_values(), fid="frame_a"))
    other = [make_value(id=f"v{i}", name=f"V{i}") for i in range(3)]
    fw_b = load_framework(write_framework(tmp_path / "b", other, fid="frame_b"))
    assert isinstance(fw_a, Framework) and isinstance(fw_b, Framework)
    assert fw_a.id == "frame_a" and fw_b.id == "frame_b"
    assert {v.framework for v in fw_a.values} == {"frame_a"}
    assert {v.framework for v in fw_b.values} == {"frame_b"}
    assert {v.id for v in fw_a.values}.isdisjoint({v.id for v in fw_b.values})


def test_duplicate_opposes_rejected(tmp_path: Path) -> None:
    values = toy_values()
    values[2]["opposes"] = ["beta", "beta"]
    path = write_framework(tmp_path, values)
    with pytest.raises(ValueError, match="duplicate opposes entry 'beta'"):
        load_framework(path)


def test_childless_group_is_leaf_documented(tmp_path: Path) -> None:
    values = [*toy_values(), make_value(id="group_c", name="Group C", definition="Nobody here.")]
    fw = load_framework(write_framework(tmp_path, values))
    assert "group_c" in [v.id for v in fw.leaves()]
    assert "group_c" not in [v.id for v in fw.groups()]
    doc = Framework.leaves.__doc__ or ""
    assert "no children" in doc and "even" in doc


def test_duplicate_yaml_key_rejected(tmp_path: Path) -> None:
    path = write_framework(tmp_path, toy_values())
    text = path.read_text(encoding="utf-8").replace("id: toy\n", "id: toy\nid: toy\n", 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate key 'id'"):
        load_framework(path)


def test_schwartz19_shape() -> None:
    fw = load_framework(FRAMEWORK_DIR / "schwartz19.yaml")
    assert len(fw.leaves()) == 19
    assert len(fw.groups()) == 4
    assert fw.level_ids()[0] == LEAF_LEVEL
    assert {"basic10", "basic10_validation", "group4"} <= set(fw.level_ids())
    assert len(fw.target_set("basic10").ids()) == 10
    assert fw.target_set("group4").ids() == [g.id for g in fw.groups()]
    for t in fw.target_set("basic10").targets:
        assert t.examples_endorse and t.examples_reject, t.id
    leaf_to_parent = {v.id: v.parent for v in fw.leaves()}
    assert fw.rollup_map("group4") == leaf_to_parent
    basic = fw.rollup_map("basic10")
    validation = fw.rollup_map("basic10_validation")
    assert {k for k in basic if basic[k] != validation[k]} == {"humility"}
    assert basic["face"] == validation["face"] == "security"
