"""Word-list baseline: a MENTION wherever a target's stems occur in English text."""

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path

import yaml

from semval.tagging.base import PromptInfo, RawTag, TagBatchResult, TaggerKind, TaggerSpec
from semval.tagging.registry import TaggerContext, register_tagger
from semval.tags import Stance
from semval.targets import TargetSet
from semval.units import DocumentMeta, Segment

DEFAULT_LEXICON_PATH = Path("data/lexicon/basic10_seed.yaml")
LEXICON_FILE_OPTION = "lexicon_file"


class LexiconTagger:
    """English only: segments whose document language is not ``en`` get an empty tag list.
    ``documents`` (keyed by document id) must cover every segment. Without a ``spec`` the
    tagger makes one from the file's framework and level."""

    def __init__(self, path: Path, spec: TaggerSpec | None = None):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.framework_id: str = data["framework_id"]
        self.level_id: str = data["level_id"]
        self.stems: dict[str, list[str]] = data["targets"]
        self.patterns = {
            tid: re.compile(
                r"\b(?:" + "|".join(re.escape(s) for s in stems) + r")\w*", re.IGNORECASE
            )
            for tid, stems in data["targets"].items()
        }
        if spec is None:
            spec = TaggerSpec(
                kind=TaggerKind.LEXICON, framework_id=self.framework_id, level_id=self.level_id
            )
        elif (spec.framework_id, spec.level_id) != (self.framework_id, self.level_id):
            raise ValueError(
                f"lexicon file {path} is for {self.framework_id}/{self.level_id}, "
                f"the spec for {spec.framework_id}/{spec.level_id}"
            )
        self.spec = spec

    def prompt_info(self, targets: TargetSet) -> PromptInfo:
        """The word lists stand in for a prompt: their hash identifies the run's method."""
        blob = json.dumps(self.stems, sort_keys=True, ensure_ascii=False)
        return PromptInfo(prompt_sha256=hashlib.sha256(blob.encode("utf-8")).hexdigest())

    def tag(
        self,
        segments: list[Segment],
        texts: dict[str, str],
        targets: TargetSet,
        documents: Mapping[str, DocumentMeta],
    ) -> TagBatchResult:
        if targets.level_id != self.level_id or targets.framework_id != self.framework_id:
            raise ValueError(
                f"lexicon is for {self.framework_id}/{self.level_id}, "
                f"targets are {targets.framework_id}/{targets.level_id}"
            )
        wanted = set(targets.ids())
        out: dict[str, list[RawTag]] = {}
        for seg in segments:
            out[seg.id] = []
            meta = documents.get(seg.document_id)
            if meta is None:
                raise ValueError(f"no document metadata for {seg.document_id!r}")
            if meta.language != "en":
                continue
            for tid, pat in self.patterns.items():
                if tid not in wanted:
                    continue
                quotes = list(dict.fromkeys(m.group(0) for m in pat.finditer(texts[seg.id])))
                if quotes:
                    out[seg.id].append(RawTag(value_id=tid, stance=Stance.MENTION, quotes=quotes))
        return TagBatchResult(tags_by_segment=out)


def _build(spec: TaggerSpec, ctx: TaggerContext) -> LexiconTagger:
    """The word list is ``options["lexicon_file"]``, else ``DEFAULT_LEXICON_PATH``; an
    absent option stays absent, so specs of runs made before options existed still match."""
    if extra := sorted(set(spec.options) - {LEXICON_FILE_OPTION}):
        raise ValueError(f"the lexicon tagger takes only {LEXICON_FILE_OPTION!r}, not {extra}")
    path = spec.options.get(LEXICON_FILE_OPTION, DEFAULT_LEXICON_PATH)
    return LexiconTagger(Path(str(path)), spec)


register_tagger(
    TaggerKind.LEXICON.value, _build, allows=frozenset({"unit", "options"}), baseline=True
)
