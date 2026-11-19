"""The tagging prompt and output schema, built only from a ``TargetSet`` and few-shot data.

The system prompt is the stable, cacheable part (instructions, definitions, examples);
the per-document part goes in the user message (``user_message``).
"""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import Any, get_args

from pydantic import BaseModel, ConfigDict, Field

from semval.tagging.base import DefinitionWording, RawTag
from semval.targets import TargetDef, TargetSet
from semval.units import DocumentMeta

STANCES: tuple[str, ...] = get_args(RawTag.model_fields["stance"].annotation)
MAX_QUOTES = 3

INSTRUCTIONS = f"""\
You tag newspaper opinion texts with human values.

For each value listed below that the text engages with, report the author's stance:
- endorse: the author promotes or defends the value. This includes lamenting that it is \
threatened or neglected.
- reject: the author opposes or dismisses the value.
- mention: the value is discussed without a clear authorial stance.

The stance is the author's own. A view the author only reports or quotes is a mention, \
unless the author takes it up.

Tag only values the text actually engages with. A text may engage with none; then return \
an empty "tags" list.

For each tag give 1 to {MAX_QUOTES} quotes that show the stance. Every quote must be copied \
verbatim from the text: an exact substring, in the text's own language, not translated, \
not shortened with ellipses. Keep quotes short (a clause or a sentence).

Give each tag a confidence between 0 and 1.

The value definitions are in English; the texts may be in any language."""


class FewShotExample(BaseModel):
    """A worked example for the prompt; ``source`` is the attribution shown with it."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    language: str
    tags: list[RawTag]
    source: str = Field(min_length=1)


@dataclass(frozen=True)
class PromptParts:
    system: str
    schema: dict[str, Any]
    # Count of targets per DefinitionWording value.
    definition_wording: dict[str, int]


def output_schema(targets: TargetSet) -> dict[str, Any]:
    """JSON schema for one answer. Uses only the structured-output subset the API supports:
    the quote cap and the confidence range are stated in descriptions and enforced after."""
    tag = {
        "type": "object",
        "properties": {
            "value_id": {"type": "string", "enum": targets.ids()},
            "stance": {"type": "string", "enum": list(STANCES)},
            "quotes": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": f"1 to {MAX_QUOTES} verbatim substrings of the text.",
            },
            "confidence": {"type": "number", "description": "Between 0 and 1."},
        },
        "required": ["value_id", "stance", "quotes", "confidence"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"tags": {"type": "array", "items": tag}},
        "required": ["tags"],
        "additionalProperties": False,
    }


def _definition(t: TargetDef) -> tuple[str, DefinitionWording]:
    if t.official is not None and t.official.text is not None:
        return t.official.text, DefinitionWording.OFFICIAL
    return t.definition, DefinitionWording.FALLBACK


def _value_block(t: TargetDef, text: str) -> str:
    lines = [f'<value id="{t.id}">', f"Name: {t.name}", f"Definition: {text}"]
    lines += [f"Example of endorsing: {e}" for e in t.examples_endorse]
    lines += [f"Example of rejecting: {e}" for e in t.examples_reject]
    lines.append("</value>")
    return "\n".join(lines)


def _answer_json(tags: list[RawTag]) -> str:
    return json.dumps({"tags": [t.model_dump(exclude_none=True) for t in tags]}, ensure_ascii=False)


def _example_block(ex: FewShotExample, ids: set[str]) -> str:
    for t in ex.tags:
        if t.value_id not in ids:
            raise ValueError(f"few-shot example {ex.id!r} uses value {t.value_id!r}, not a target")
        for q in t.quotes:
            if q not in ex.text:
                raise ValueError(f"few-shot example {ex.id!r}: quote {q!r} is not in its text")
    return "\n".join(
        [
            f'<example id="{ex.id}">',
            f"Source: {ex.source}",
            f"Language: {ex.language}",
            f"<text>\n{ex.text}\n</text>",
            f"Answer: {_answer_json(ex.tags)}",
            "</example>",
        ]
    )


def build_prompt(targets: TargetSet, few_shot: list[FewShotExample]) -> PromptParts:
    wording: Counter[str] = Counter()
    blocks = []
    for t in targets.targets:
        text, kind = _definition(t)
        wording[kind.value] += 1
        blocks.append(_value_block(t, text))
    parts = [INSTRUCTIONS, "Values:\n\n" + "\n\n".join(blocks)]
    if few_shot:
        ids = set(targets.ids())
        examples = "\n\n".join(_example_block(ex, ids) for ex in few_shot)
        parts.append("Worked examples, each with its source:\n\n" + examples)
    return PromptParts(
        system="\n\n".join(parts), schema=output_schema(targets), definition_wording=dict(wording)
    )


def user_message(text: str, meta: DocumentMeta) -> str:
    return f"Language: {meta.language}\nGenre: {meta.genre}\n\n<text>\n{text}\n</text>"


def prompt_sha256(parts: PromptParts) -> str:
    """Hash of the system prompt text plus the schema JSON (canonical key order)."""
    blob = parts.system + "\n" + json.dumps(parts.schema, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
