"""The few-shot example set: loading, writing with attribution, finalising owner verdicts,
and rolling examples up to a coarser value level.

``data/fewshot/touche23.yaml`` is a mapping: an ``attribution`` header (Touché23-ValueEval is
CC BY 4.0) and the ``examples`` list. Examples are written at leaf level; ``fewshot_at_level``
adapts them to the level of a run.
"""

import logging
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from semval.datasets.touche23 import ToucheItem
from semval.fsutil import atomic_write_text
from semval.review.labels import LabelRecord, Verdict
from semval.tagging.base import RawTag
from semval.tagging.fewshot_candidates import Candidate, select_candidates  # noqa: F401
from semval.tagging.prompt import MAX_QUOTES, FewShotExample
from semval.tags import Stance, ValueTag, rollup_tags
from semval.values import LEAF_LEVEL, Framework

log = logging.getLogger(__name__)

DEFAULT_FEWSHOT_PATH = Path("data/fewshot/touche23.yaml")
FEWSHOT_RUN_ID = "fewshot"
ATTRIBUTION: dict[str, str] = {
    "dataset": "Touché23-ValueEval",
    "citation": (
        "Kiesel, Alshomary, Mirzakhmedova, Heinrich, Handke, Wachsmuth, Stein (2023). "
        "SemEval-2023 Task 4: ValueEval: Identification of Human Values behind Arguments."
    ),
    "licence": "CC BY 4.0",
    "url": "https://zenodo.org/record/7879430",
    "changes": "Arguments rendered as conclusion, stance and premise; the value stances and "
    "quotes below are not part of the dataset.",
    "stances": "Stances drafted by Claude Opus 5.5 and confirmed by the project owner.",
}
SOURCE_TEMPLATE = "Touché23-ValueEval (CC BY 4.0), argument {id}"


def load_fewshot(path: Path) -> list[FewShotExample]:
    """A YAML list of examples, or a mapping with an ``examples`` list."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    items = data.get("examples") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: expected a non-empty list of few-shot examples")
    return [FewShotExample.model_validate(x) for x in items]


def write_fewshot(path: Path, examples: Sequence[FewShotExample]) -> None:
    """Write the attribution header and the examples (Unicode kept, readable)."""
    doc: dict[str, Any] = {
        "attribution": dict(ATTRIBUTION),
        "examples": [e.model_dump(mode="json", exclude_none=True) for e in examples],
    }
    body = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100)
    atomic_write_text(Path(path), body)


# -- finalising ---------------------------------------------------------------------------


def _quotes(text: str, spans: Iterable[Any]) -> list[str]:
    out = [text[s.start : s.end] for s in spans if 0 <= s.start < s.end <= len(text)]
    return list(dict.fromkeys(q for q in out if q.strip()))[:MAX_QUOTES]


def finalize(
    candidates: Sequence[Candidate],
    items: Mapping[str, ToucheItem],
    labels: Iterable[LabelRecord],
    labeller: str,
) -> list[FewShotExample]:
    """Apply ``labeller``'s verdicts (leaf level) to the candidates.

    correct keeps the drafted tag, wrong_call takes the corrected stance, not_present drops
    the tag, added adds a tag quoting the owner's evidence spans. A candidate the labeller
    never judged is dropped; a judged one may end with no tags (a valid empty answer). A
    drafted tag with no verdict in a judged candidate is dropped too: nothing unconfirmed
    goes into the prompt.
    """
    by_doc: dict[str, dict[str, LabelRecord]] = {}
    for r in labels:
        if r.labeller == labeller and r.level_id == LEAF_LEVEL:
            by_doc.setdefault(r.document_id, {})[r.value_id] = r
    out = []
    for cand in candidates:
        judged = by_doc.get(cand.id)
        if not judged:
            log.info("finalize: %s not judged, dropped", cand.id)
            continue
        text = items[cand.id].text
        tags: list[RawTag] = []
        for tag in cand.tags:
            rec = judged.get(tag.value_id)
            if rec is None:
                log.warning("finalize: %s %s has no verdict, dropped", cand.id, tag.value_id)
                continue
            stance = rec.present_stance()
            if stance is not None:
                tags.append(tag.model_copy(update={"stance": stance.value}))
        drafted = {t.value_id for t in cand.tags}
        for value_id, rec in judged.items():
            if value_id not in drafted and rec.verdict == Verdict.ADDED:
                stance = rec.corrected_stance
                assert stance is not None  # LabelRecord guarantees it for ADDED
                quotes = _quotes(text, rec.owner_evidence)
                tags.append(RawTag(value_id=value_id, stance=stance.value, quotes=quotes))
        out.append(
            FewShotExample(
                id=cand.id,
                text=text,
                language="en",
                tags=tags,
                source=SOURCE_TEMPLATE.format(id=cand.id),
            )
        )
    return out


def stance_counts(examples: Iterable[FewShotExample]) -> dict[str, int]:
    """Tags per stance over the examples (endorse, reject, mention)."""
    c = Counter(t.stance for e in examples for t in e.tags)
    return {s: c.get(s, 0) for s in ("endorse", "reject", "mention")}


# -- level adapter ------------------------------------------------------------------------


def fewshot_at_level(
    examples: Sequence[FewShotExample], framework: Framework, level_id: str
) -> list[FewShotExample]:
    """The examples with leaf tags rolled up to ``level_id``'s targets.

    Tags that land on one target are combined with the framework's own rule (``rollup_tags``):
    endorse beats reject beats mention, quotes are pooled, and a target that gets both
    endorse and reject is dropped from that example (logged).
    """
    if level_id == LEAF_LEVEL:
        return list(examples)
    rollup = framework.rollup_map(level_id)
    out = []
    for ex in examples:
        unknown = [t.value_id for t in ex.tags if t.value_id not in rollup]
        if unknown:
            raise ValueError(f"few-shot example {ex.id!r}: {unknown} are not leaves of {level_id}")
        tags = [
            ValueTag(
                segment_id=ex.id,
                value_id=t.value_id,
                stance=Stance(t.stance),
                confidence=t.confidence,
                run_id=FEWSHOT_RUN_ID,
            )
            for t in ex.tags
        ]
        quotes: dict[str, list[str]] = {}
        for t in ex.tags:
            quotes.setdefault(rollup[t.value_id], []).extend(t.quotes)
        kept = []
        for combined in rollup_tags(tags, rollup):
            if combined.stance == Stance.CONTESTED:
                log.warning(
                    "few-shot %s: %s is both endorsed and rejected at %s, dropped",
                    ex.id, combined.value_id, level_id,
                )  # fmt: skip
                continue
            qs = list(dict.fromkeys(quotes[combined.value_id]))[:MAX_QUOTES]
            kept.append(
                RawTag(
                    value_id=combined.value_id,
                    stance=combined.stance.value,  # type: ignore[arg-type]
                    quotes=qs,
                    confidence=combined.confidence,
                )
            )
        out.append(ex.model_copy(update={"tags": kept}))
    return out
