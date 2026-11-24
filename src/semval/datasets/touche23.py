"""Touché23-ValueEval: labelled English arguments with the 20 level-2 value categories.

Source: Mirzakhmedova et al. (2023), CC BY 4.0. The data is not in the Hugging Face repo
(``webis/Touche23-ValueEval`` holds only a loading script, which we never run); the script
itself points at Zenodo record 7879430, so ``download`` fetches the raw TSVs from there.

Labels are 0/1 per category (no attained/constrained stance in 2023). 19 categories are
framework leaves; "Universalism: objectivity" has no leaf and is kept as a flag that
``gold_at_level`` adds only at the levels in ``OBJECTIVITY_TARGET``.

``build_greek_proxy`` machine-translates a seeded sample of items into Greek (a test set for
Greek), through the cost ledger. Proxy items keep the English ids and labels.
"""

import csv
import json
import logging
import random
import time
import urllib.request
from pathlib import Path
from typing import Any, Final, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from semval.config import (
    MAX_TOKENS_BY_EFFORT,
    SONNET_5_5,
    Effort,
)
from semval.fsutil import atomic_write_text
from semval.models import registry
from semval.review.texts import DocInfo, TextUnavailable
from semval.tagging.base import Usage
from semval.tagging.ledger import BudgetExceeded, CostLedger, cost_of
from semval.values import LEAF_LEVEL, Framework

log = logging.getLogger(__name__)

USER_AGENT = "semval-research/0.1 (+https://github.com/kosnikos/semantic-values)"
ZENODO_BASE = "https://zenodo.org/record/7879430/files/"
DEFAULT_DIR = Path("data/external/touche23")
PROXY_FILE = "proxy_el.jsonl"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
PROXY_MODEL = SONNET_5_5
PROXY_EFFORT = Effort.LOW
PROXY_RUN_ID = "touche23-proxy-el"
EST_OUTPUT_TOKENS = 1000  # for the pre-call budget check
CHARS_PER_TOKEN = 3.5
REQUEST_PAUSE_SECONDS = 1.0

Split = Literal["train", "validation", "test"]
_FILE_STEM: Final[dict[str, str]] = {
    "train": "training",
    "validation": "validation",
    "test": "test",
}
DOWNLOAD_FILES: Final[tuple[str, ...]] = tuple(
    f"{kind}-{stem}.tsv" for stem in _FILE_STEM.values() for kind in ("arguments", "labels")
)

# The 20 level-2 categories in file column order -> framework leaf id (None: no leaf).
TOUCHE23_CATEGORIES: Final[dict[str, str | None]] = {
    "Self-direction: thought": "self_direction_thought",
    "Self-direction: action": "self_direction_action",
    "Stimulation": "stimulation",
    "Hedonism": "hedonism",
    "Achievement": "achievement",
    "Power: dominance": "power_dominance",
    "Power: resources": "power_resources",
    "Face": "face",
    "Security: personal": "security_personal",
    "Security: societal": "security_societal",
    "Tradition": "tradition",
    "Conformity: rules": "conformity_rules",
    "Conformity: interpersonal": "conformity_interpersonal",
    "Humility": "humility",
    "Benevolence: caring": "benevolence_caring",
    "Benevolence: dependability": "benevolence_dependability",
    "Universalism: concern": "universalism_concern",
    "Universalism: nature": "universalism_nature",
    "Universalism: tolerance": "universalism_tolerance",
    "Universalism: objectivity": None,
}
OBJECTIVITY_FLAG: Final = "objectivity"
# Level id -> the target that "Universalism: objectivity" counts toward at that level.
OBJECTIVITY_TARGET: Final[dict[str, str]] = {"basic10": "universalism"}

Language = Literal["en", "el"]
_STANCE_EN: Final = {"in favor of": "in favor of", "against": "against"}
_STANCE_EL: Final = {"in favor of": "υπέρ", "against": "κατά"}
_FIELD_NAMES: Final[dict[str, tuple[str, str, str]]] = {
    "en": ("Conclusion", "Stance", "Premise"),
    "el": ("Συμπέρασμα", "Στάση", "Προκείμενη"),
}
PROXY_ID_PREFIX: Final = "el:"  # document id of a proxy item in the text provider


class ToucheItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    conclusion: str
    stance: Literal["in favor of", "against"]  # the dataset's own (English) value
    premise: str
    labels: set[str]  # leaf ids, plus OBJECTIVITY_FLAG
    language: Language = "en"

    @property
    def text(self) -> str:
        """Deterministic rendering: conclusion, stance, premise (stance word per language)."""
        c, s, p = _FIELD_NAMES[self.language]
        stance = (_STANCE_EL if self.language == "el" else _STANCE_EN)[self.stance]
        return f"{c}: {self.conclusion}\n{s}: {stance}\n{p}: {self.premise}"


# -- download -----------------------------------------------------------------------------


def download(
    out_dir: Path = DEFAULT_DIR,
    base_url: str = ZENODO_BASE,
    pause: float = REQUEST_PAUSE_SECONDS,
    files: tuple[str, ...] = DOWNLOAD_FILES,
) -> list[Path]:
    """Fetch the raw TSVs one at a time, with our User-Agent. Never runs the loading script."""
    paths = []
    for i, name in enumerate(files):
        if i:
            time.sleep(pause)
        req = urllib.request.Request(base_url + name, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
        path = Path(out_dir) / name
        atomic_write_text(path, body)
        log.info("downloaded %s (%d bytes)", name, len(body))
        paths.append(path)
    return paths


# -- loading ------------------------------------------------------------------------------


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def load_split(split: Split, data_dir: Path = DEFAULT_DIR) -> list[ToucheItem]:
    """The items of one split, in file order, from the downloaded TSVs."""
    stem = _FILE_STEM[split]
    args = _read_tsv(Path(data_dir) / f"arguments-{stem}.tsv")
    labels = {r["Argument ID"]: r for r in _read_tsv(Path(data_dir) / f"labels-{stem}.tsv")}
    items = []
    for row in args:
        lab = labels.get(row["Argument ID"])
        if lab is None:
            raise ValueError(f"{split}: no labels for {row['Argument ID']}")
        flags: set[str] = set()
        for category, leaf in TOUCHE23_CATEGORIES.items():
            if lab[category] not in ("0", "1"):
                raise ValueError(f"{split} {row['Argument ID']}: bad label {lab[category]!r}")
            if lab[category] == "1":
                flags.add(leaf or OBJECTIVITY_FLAG)
        items.append(
            ToucheItem(
                id=row["Argument ID"],
                conclusion=row["Conclusion"],
                stance=row["Stance"],  # type: ignore[arg-type]
                premise=row["Premise"],
                labels=flags,
            )
        )
    return items


def gold_at_level(item: ToucheItem, framework: Framework, level_id: str) -> set[str]:
    """The item's gold targets at ``level_id``: leaves rolled up by the framework's map;
    objectivity counts only at the levels in ``OBJECTIVITY_TARGET``."""
    rollup = framework.rollup_map(level_id)
    gold = {rollup[v] for v in item.labels if v in rollup}
    if OBJECTIVITY_FLAG in item.labels and level_id != LEAF_LEVEL:
        target = OBJECTIVITY_TARGET.get(level_id)
        if target is not None:
            gold.add(target)
    return gold


# -- Greek proxy --------------------------------------------------------------------------

_SYSTEM = (
    "You translate short argument texts from English into Greek (modern standard Greek, "
    "natural and faithful, same register, no added commentary). You get an argument's "
    "conclusion and premise; translate each, keeping meaning, tone and any names, numbers "
    "and quotation marks. Answer only in the requested JSON."
)
_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {"conclusion": {"type": "string"}, "premise": {"type": "string"}},
    "required": ["conclusion", "premise"],
    "additionalProperties": False,
}


class Translator(Protocol):
    def __call__(self, conclusion: str, premise: str) -> tuple[str, str]: ...


class TranslationFailed(Exception):
    """The model's answer for one item was unusable (refused, truncated, malformed)."""


def billed(msg: Any, default_model: str = PROXY_MODEL) -> list[tuple[str, Usage]]:
    """(model name, usage) per billed attempt, as the tagger counts them."""
    iterations = getattr(msg.usage, "iterations", None)
    pairs = (
        [(getattr(it, "model", None) or str(default_model), it) for it in iterations]
        if iterations
        else [(msg.model if isinstance(msg.model, str) else str(default_model), msg.usage)]
    )
    return [
        (
            str(model),
            Usage(
                input_tokens=u.input_tokens or 0,
                output_tokens=u.output_tokens or 0,
                cache_creation_input_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
                cache_read_input_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            ),
        )
        for model, u in pairs
    ]


class ClaudeTranslator:
    """English -> Greek with Claude through the ledger: every call is checked against the
    budget before it is made and recorded after, refusals and unusable answers included."""

    def __init__(self, client: Any, ledger: CostLedger, run_id: str = PROXY_RUN_ID) -> None:
        self.client, self.ledger, self.run_id = client, ledger, run_id

    def _estimate(self, params: dict[str, Any]) -> float:
        chars = len(_SYSTEM) + len(params["messages"][0]["content"])
        in_tokens = int(chars / CHARS_PER_TOKEN) + 1
        usage = Usage(input_tokens=in_tokens, output_tokens=EST_OUTPUT_TOKENS)
        return cost_of(usage, PROXY_MODEL, False)

    def __call__(self, conclusion: str, premise: str) -> tuple[str, str]:
        content = json.dumps({"conclusion": conclusion, "premise": premise}, ensure_ascii=False)
        params: dict[str, Any] = {
            "model": str(PROXY_MODEL),
            "max_tokens": MAX_TOKENS_BY_EFFORT[PROXY_EFFORT],
            "system": [{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": content}],
            "output_config": {
                "effort": str(PROXY_EFFORT),
                "format": {"type": "json_schema", "schema": _SCHEMA},
            },
        }
        if registry().get(PROXY_MODEL).server_fallbacks:
            params = {**params, "betas": [FALLBACK_BETA], "fallbacks": "default"}
        if not self.ledger.can_spend(self._estimate(params)):
            raise BudgetExceeded("the next translation would pass the budget cap")
        msg = self.client.beta.messages.create(**params)
        # records every billed attempt, then may raise BudgetExceeded
        self.ledger.record_all(
            self.run_id, [(registry().priced(m), u) for m, u in billed(msg)], False
        )
        if msg.stop_reason != "end_turn":
            raise TranslationFailed(f"stop_reason {msg.stop_reason}")
        text = next((b.text for b in msg.content if b.type == "text"), None)
        try:
            data = json.loads(text)  # type: ignore[arg-type]
            out = (str(data["conclusion"]).strip(), str(data["premise"]).strip())
        except (ValueError, KeyError, TypeError) as e:
            raise TranslationFailed(f"unusable answer: {e!r}") from e
        if not all(out):
            raise TranslationFailed("empty translation")
        return out


def load_proxy(data_dir: Path = DEFAULT_DIR) -> list[ToucheItem]:
    path = Path(data_dir) / PROXY_FILE
    if not path.exists():
        return []
    return [
        ToucheItem.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_greek_proxy(
    translator: Translator,
    n: int = 100,
    seed: int = 1,
    split: Split = "test",
    data_dir: Path = DEFAULT_DIR,
) -> Path:
    """Translate ``n`` items of ``split`` (seeded sample, by sorted id) into ``proxy_el.jsonl``.

    Resumable: ids already in the file are kept and skipped. An item whose translation is
    unusable is logged and left out. ``BudgetExceeded`` propagates; what was translated so
    far stays in the file.
    """
    data_dir = Path(data_dir)
    items = sorted(load_split(split, data_dir), key=lambda i: i.id)
    chosen = random.Random(seed).sample(items, min(n, len(items)))
    chosen.sort(key=lambda i: i.id)
    path = data_dir / PROXY_FILE
    done = {i.id for i in load_proxy(data_dir)}
    path.parent.mkdir(parents=True, exist_ok=True)
    skipped = 0
    for item in chosen:
        if item.id in done:
            continue
        try:
            conclusion, premise = translator(item.conclusion, item.premise)
        except TranslationFailed as e:
            log.warning("proxy: %s left out: %s", item.id, e)
            skipped += 1
            continue
        greek = item.model_copy(
            update={"conclusion": conclusion, "premise": premise, "language": "el"}
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(greek.model_dump_json() + "\n")
    if skipped:
        log.warning("proxy: %d items left out; rerun to retry them", skipped)
    return path


# -- review text provider -----------------------------------------------------------------


class ToucheTextProvider:
    """``TextProvider`` over Touché items. English items are keyed by their id; proxy items
    by ``PROXY_ID_PREFIX`` + id (the ids are shared with the originals)."""

    def __init__(self, english: list[ToucheItem], proxy: list[ToucheItem] | None = None) -> None:
        self._items = {i.id: i for i in english}
        self._items.update({PROXY_ID_PREFIX + i.id: i for i in proxy or []})

    def _item(self, document_id: str) -> ToucheItem:
        item = self._items.get(document_id)
        if item is None:
            raise TextUnavailable(f"{document_id} is not a loaded Touché23 item")
        return item

    def text(self, document_id: str) -> str:
        return self._item(document_id).text

    def info(self, document_id: str) -> DocInfo:
        item = self._item(document_id)
        return DocInfo(
            title=item.conclusion, source_id="touche23", genre="argument", language=item.language
        )
