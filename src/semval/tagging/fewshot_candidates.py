"""Few-shot candidates: pick Touché23 items, let Claude draft their stances, keep the drafts.

Selection uses the train and validation splits only (the test split is our evaluation set).
The draft is a stance (endorse, reject, mention) and verbatim quotes for each value the
dataset's annotators marked present; the project owner then confirms or corrects it in the
review page (see ``fewshot`` for the finalising step). Drafts go to a git-ignored JSONL.
"""

import json
import logging
import random
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from semval.config import (
    MAX_TOKENS_BY_EFFORT,
    SERVER_FALLBACK_MODELS,
    Effort,
    ModelId,
    priced_model,
)
from semval.datasets.touche23 import (
    CHARS_PER_TOKEN,
    DEFAULT_DIR,
    EST_OUTPUT_TOKENS,
    OBJECTIVITY_FLAG,
    ToucheItem,
    billed,
    load_split,
)
from semval.tagging.base import RawTag, Usage
from semval.tagging.claude import FALLBACK_BETA
from semval.tagging.ledger import BudgetExceeded, CostLedger, cost_of
from semval.tagging.prompt import MAX_QUOTES, build_prompt, output_schema
from semval.targets import TargetSet

log = logging.getLogger(__name__)

CANDIDATES_FILE = "fewshot_candidates.jsonl"
CANDIDATES_RUN_ID = "touche23-fewshot-candidates"  # ledger run id and review "source run"
DRAFT_MODEL = ModelId.OPUS_5_5
DRAFT_EFFORT = Effort.MEDIUM
SELECTION_SPLITS: tuple[Literal["train", "validation"], ...] = ("train", "validation")

DRAFT_ADDENDUM = """\
Drafting mode: the user message gives one text and the values that human annotators marked as \
present in it. For each of those values, give your stance and 1 to {max_quotes} verbatim quotes. \
If you think the text does not really express one of them, leave it out of "tags". Never add \
a value that is not on the list."""


class Candidate(BaseModel):
    """One drafted few-shot candidate. No text: it is rendered from the dataset item."""

    model_config = ConfigDict(extra="forbid")

    id: str
    split: Literal["train", "validation"]
    tags: list[RawTag] = Field(default_factory=list)


class DraftFailed(Exception):
    """The model's answer for one item was unusable (refused, truncated, malformed)."""


class Drafter(Protocol):
    def __call__(self, item: ToucheItem) -> list[RawTag]: ...


def leaf_gold(item: ToucheItem) -> list[str]:
    """The item's gold leaf values (objectivity has no leaf), sorted."""
    return sorted(item.labels - {OBJECTIVITY_FLAG})


def select_candidates(n: int = 20, seed: int = 1, data_dir: Path = DEFAULT_DIR) -> list[ToucheItem]:
    """``n`` items from train+validation, covering the leaf values as evenly as possible.

    Deterministic for a seed. Greedy: repeatedly take the least-covered value that still has
    an unchosen item, and from its items the one whose other values are least covered.
    Items with no leaf label (objectivity only, or none) are never chosen.
    """
    pool = {i.id: i for s in SELECTION_SPLITS for i in load_split(s, data_dir) if leaf_gold(i)}
    order = sorted(pool)
    random.Random(seed).shuffle(order)
    rank = {iid: r for r, iid in enumerate(order)}
    count: dict[str, int] = {v: 0 for i in pool.values() for v in leaf_gold(i)}
    chosen: list[ToucheItem] = []
    left = set(pool)
    while len(chosen) < n and left:
        open_values = {v for iid in left for v in leaf_gold(pool[iid])}
        value = min(open_values, key=lambda v: (count[v], v))
        best = min(
            (iid for iid in left if value in pool[iid].labels),
            key=lambda iid: (sum(count[v] for v in leaf_gold(pool[iid])), rank[iid]),
        )
        left.discard(best)
        chosen.append(pool[best])
        for v in leaf_gold(pool[best]):
            count[v] += 1
    return chosen


class FewShotDrafter:
    """Drafts stances and quotes with Claude through the ledger: each call is checked against
    the budget before it is made and recorded after, refusals and unusable answers included."""

    def __init__(
        self, client: Any, ledger: CostLedger, targets: TargetSet, run_id: str = CANDIDATES_RUN_ID
    ) -> None:
        self.client, self.ledger, self.run_id = client, ledger, run_id
        parts = build_prompt(targets, [])
        self.system = parts.system + "\n\n" + DRAFT_ADDENDUM.format(max_quotes=MAX_QUOTES)
        self.schema = output_schema(targets)

    @staticmethod
    def _user(item: ToucheItem) -> str:
        values = ", ".join(leaf_gold(item))
        return f"<text>\n{item.text}\n</text>\n\nValues the annotators marked as present: {values}"

    def _estimate(self, params: dict[str, Any]) -> float:
        chars = len(self.system) + len(params["messages"][0]["content"])
        usage = Usage(
            input_tokens=int(chars / CHARS_PER_TOKEN) + 1, output_tokens=EST_OUTPUT_TOKENS
        )
        return cost_of(usage, DRAFT_MODEL, False)

    def __call__(self, item: ToucheItem) -> list[RawTag]:
        params: dict[str, Any] = {
            "model": str(DRAFT_MODEL),
            "max_tokens": MAX_TOKENS_BY_EFFORT[DRAFT_EFFORT],
            "system": [
                {"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}
            ],
            "messages": [{"role": "user", "content": self._user(item)}],
            "output_config": {
                "effort": str(DRAFT_EFFORT),
                "format": {"type": "json_schema", "schema": self.schema},
            },
        }
        if DRAFT_MODEL in SERVER_FALLBACK_MODELS:
            params = {**params, "betas": [FALLBACK_BETA], "fallbacks": "default"}
        if not self.ledger.can_spend(self._estimate(params)):
            raise BudgetExceeded("the next draft would pass the budget cap")
        msg = self.client.beta.messages.create(**params)
        pairs = [(priced_model(m), u) for m, u in billed(msg, DRAFT_MODEL)]
        self.ledger.record_all(self.run_id, pairs, False)  # all recorded, then may raise
        if msg.stop_reason != "end_turn":
            raise DraftFailed(f"stop_reason {msg.stop_reason}")
        text = next((b.text for b in msg.content if b.type == "text"), None)
        try:
            raw = [RawTag.model_validate(x) for x in json.loads(text)["tags"]]  # type: ignore[arg-type]
        except (ValueError, KeyError, TypeError, ValidationError) as e:
            raise DraftFailed(f"unusable answer: {e!r}") from e
        return _checked(item, raw)


def _checked(item: ToucheItem, raw: list[RawTag]) -> list[RawTag]:
    """Keep tags for gold values only (once each); drop quotes that are not in the text."""
    gold, seen, out = set(leaf_gold(item)), set(), []
    for tag in raw:
        if tag.value_id not in gold or tag.value_id in seen:
            log.warning(
                "draft %s: ignoring %s (not a gold value, or repeated)", item.id, tag.value_id
            )
            continue
        seen.add(tag.value_id)
        quotes = []
        for q in tag.quotes[:MAX_QUOTES]:
            if q and q in item.text:
                quotes.append(q)
            else:
                log.warning("draft %s: dropping quote not in the text: %r", item.id, q)
        out.append(tag.model_copy(update={"quotes": quotes}))
    return out


def load_candidates(data_dir: Path = DEFAULT_DIR) -> list[Candidate]:
    path = Path(data_dir) / CANDIDATES_FILE
    if not path.exists():
        return []
    return [
        Candidate.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def draft_candidates(
    drafter: Drafter, items: list[ToucheItem], data_dir: Path = DEFAULT_DIR
) -> Path:
    """Draft each item not already in ``fewshot_candidates.jsonl`` and append it (resumable).

    An item whose draft is unusable is logged and left out; a rerun retries it.
    ``BudgetExceeded`` propagates; what was drafted so far stays in the file.
    """
    path = Path(data_dir) / CANDIDATES_FILE
    done = {c.id for c in load_candidates(data_dir)}
    path.parent.mkdir(parents=True, exist_ok=True)
    train_ids = {i.id for i in load_split("train", data_dir)}
    skipped = 0
    for item in items:
        if item.id in done:
            continue
        try:
            tags = drafter(item)
        except DraftFailed as e:
            log.warning("candidates: %s left out: %s", item.id, e)
            skipped += 1
            continue
        split = "train" if item.id in train_ids else "validation"
        cand = Candidate(id=item.id, split=split, tags=tags)
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(cand.model_dump_json() + "\n")
    if skipped:
        log.warning("candidates: %d items left out; rerun to retry them", skipped)
    return path
