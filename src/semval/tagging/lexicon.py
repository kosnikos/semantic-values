"""Word-list baseline: a MENTION wherever a target's stems occur in English text."""

import re
from collections.abc import Mapping
from pathlib import Path

import yaml

from semval.tagging.base import RawTag, TagBatchResult, TaggerKind, TaggerSpec
from semval.targets import TargetSet
from semval.units import Segment, UnitLevel


class LexiconTagger:
    """``languages`` maps document id to language code; segments of any document not
    marked ``en`` (including unknown ones) are skipped and get an empty tag list."""

    def __init__(self, path: Path, languages: Mapping[str, str], unit: UnitLevel):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.framework_id: str = data["framework_id"]
        self.level_id: str = data["level_id"]
        self.patterns = {
            tid: re.compile(
                r"\b(?:" + "|".join(re.escape(s) for s in stems) + r")\w*", re.IGNORECASE
            )
            for tid, stems in data["targets"].items()
        }
        self.languages = languages
        self.spec = TaggerSpec(
            kind=TaggerKind.LEXICON,
            framework_id=self.framework_id,
            level_id=self.level_id,
            unit=unit,
        )

    def tag(
        self, segments: list[Segment], texts: dict[str, str], targets: TargetSet
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
            if self.languages.get(seg.document_id) != "en":
                continue
            for tid, pat in self.patterns.items():
                if tid not in wanted:
                    continue
                quotes = list(dict.fromkeys(m.group(0) for m in pat.finditer(texts[seg.id])))
                if quotes:
                    out[seg.id].append(RawTag(value_id=tid, stance="mention", quotes=quotes))
        return TagBatchResult(tags_by_segment=out)
