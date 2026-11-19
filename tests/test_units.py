import pytest

from semval.units import UnitLevel, segment

TEXT = "Πρώτη πρόταση. Δεύτερη!  Third one?\n\nΝέα παράγραφος εδώ. Τέλος"


def test_rank_order():
    assert [lv.rank for lv in UnitLevel] == [0, 1, 2]


def test_offsets_reconstruct_and_trimmed():
    segs = segment("d1", TEXT, UnitLevel.SENTENCE)
    for s in segs:
        piece = TEXT[s.start : s.end]
        assert piece == piece.strip() and piece
    sents = [TEXT[s.start : s.end] for s in segs if s.level is UnitLevel.SENTENCE]
    assert sents == [
        "Πρώτη πρόταση.",
        "Δεύτερη!",
        "Third one?",
        "Νέα παράγραφος εδώ.",
        "Τέλος",
    ]


def test_ids_and_parents():
    segs = {s.id: s for s in segment("d1", TEXT, UnitLevel.SENTENCE)}
    assert segs["d1:a"].parent_id is None
    assert segs["d1:p0"].parent_id == "d1:a"
    assert segs["d1:p1:s1"].parent_id == "d1:p1"
    assert segs["d1:p0:s2"].level is UnitLevel.SENTENCE
    assert segs["d1:p1:s1"].document_id == "d1"


def test_levels_returned():
    assert {s.level for s in segment("d", TEXT, UnitLevel.ARTICLE)} == {UnitLevel.ARTICLE}
    levels = {s.level for s in segment("d", TEXT, UnitLevel.PARAGRAPH)}
    assert levels == {UnitLevel.ARTICLE, UnitLevel.PARAGRAPH}


def test_article_span_and_empty_text():
    (art,) = segment("d", "  hi  ", UnitLevel.ARTICLE)
    assert "  hi  "[art.start : art.end] == "hi"
    assert segment("d", "   ", UnitLevel.SENTENCE) == []


def test_no_split_on_lowercase_or_decimal():
    text = "Costs 3.5 euro, e.g. cheap. Done"
    sents = [
        text[s.start : s.end]
        for s in segment("d", text, UnitLevel.SENTENCE)
        if s.level is UnitLevel.SENTENCE
    ]
    assert sents == ["Costs 3.5 euro, e.g. cheap.", "Done"]


def test_segment_offsets_validated():
    from semval.units import Segment

    with pytest.raises(ValueError):
        Segment(id="x", document_id="d", level=UnitLevel.ARTICLE, parent_id=None, start=5, end=2)
