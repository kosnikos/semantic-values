"""The tagging prompt and output schema, built only from a ``TargetSet`` and few-shot data.

The system prompt is the stable, cacheable part (instructions, definitions, examples);
the per-document part goes in the user message (``user_message``).
"""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, get_args

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from semval.tagging.base import DefinitionWording, RawTag
from semval.targets import TargetDef, TargetSet
from semval.units import DocumentMeta

STANCES: tuple[str, ...] = get_args(RawTag.model_fields["stance"].annotation)
MAX_QUOTES = 3
DEFAULT_PROMPT_ID = "v1"
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "data" / "prompts"


class PromptTemplate(BaseModel):
    """A prompt file: the instructions (``{max_quotes}`` is filled in) and the user message
    template (``{language}``, ``{genre}``, ``{text}``)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    instructions: str
    user_template: str
    notes: str = ""

    def rendered_instructions(self) -> str:
        return self.instructions.format(max_quotes=MAX_QUOTES)


def load_prompt(prompt_id: str, prompts_dir: Path = PROMPTS_DIR) -> PromptTemplate:
    """The prompt in ``<prompts_dir>/<prompt_id>.yaml``; an unknown id lists the known ones."""
    path = Path(prompts_dir) / f"{prompt_id}.yaml"
    if not path.is_file():
        known = sorted(p.stem for p in Path(prompts_dir).glob("*.yaml"))
        raise ValueError(f"unknown prompt id {prompt_id!r}; known: {', '.join(known)}")
    try:
        template = PromptTemplate.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except ValidationError as e:
        raise ValueError(f"{path}: {e}") from e
    if template.id != prompt_id:
        raise ValueError(f"{path}: id {template.id!r} does not match the file name")
    return template


@cache
def _default_template() -> PromptTemplate:
    return load_prompt(DEFAULT_PROMPT_ID)


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


def build_prompt(
    targets: TargetSet, few_shot: list[FewShotExample], template: PromptTemplate | None = None
) -> PromptParts:
    template = template or _default_template()
    wording: Counter[str] = Counter()
    blocks = []
    for t in targets.targets:
        text, kind = _definition(t)
        wording[kind.value] += 1
        blocks.append(_value_block(t, text))
    parts = [template.rendered_instructions(), "Values:\n\n" + "\n\n".join(blocks)]
    if few_shot:
        ids = set(targets.ids())
        examples = "\n\n".join(_example_block(ex, ids) for ex in few_shot)
        parts.append("Worked examples, each with its source:\n\n" + examples)
    return PromptParts(
        system="\n\n".join(parts), schema=output_schema(targets), definition_wording=dict(wording)
    )


def user_message(text: str, meta: DocumentMeta, template: PromptTemplate | None = None) -> str:
    template = template or _default_template()
    return template.user_template.format(language=meta.language, genre=meta.genre, text=text)


def prompt_sha256(parts: PromptParts, template: PromptTemplate | None = None) -> str:
    """Hash of the system prompt, the user-message template and the schema JSON."""
    template = template or _default_template()
    schema = json.dumps(parts.schema, sort_keys=True, ensure_ascii=False)
    blob = f"{parts.system}\n{template.user_template}\n{schema}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
