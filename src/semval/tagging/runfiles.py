"""Where runs and their inputs live on disk, and how to read them.

Kept apart from ``runner`` so that readers of run files (the review page, evaluation) do
not import the tagger and its API SDK.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from semval.sampling.sample import (
    DEFAULT_RAW_DIR,
    DEFAULT_SAMPLES_DIR,
    SampleManifest,
    doc_text_path,
)
from semval.tagging.base import RunManifest
from semval.tags import ValueTag
from semval.units import Document
from semval.values import FRAMEWORK_DIR

DEFAULT_RUNS_DIR = Path("data/runs")
MANIFEST = "manifest.json"
TAGS = "tags.jsonl"


@dataclass(frozen=True)
class RunPaths:
    samples_dir: Path = DEFAULT_SAMPLES_DIR
    raw_dir: Path = DEFAULT_RAW_DIR
    framework_dir: Path = FRAMEWORK_DIR
    runs_dir: Path = DEFAULT_RUNS_DIR


DEFAULT_PATHS = RunPaths()


def load_sample(name: str, samples_dir: Path) -> SampleManifest:
    path = Path(samples_dir) / f"{name}.yaml"
    return SampleManifest.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def read_text(raw_dir: Path, doc: Document) -> str:
    """The cached text, byte-exact (offsets depend on it) and checked against its hash."""
    data = doc_text_path(raw_dir, doc.id).read_bytes()
    if hashlib.sha256(data).hexdigest() != doc.text_sha256:
        raise ValueError(f"cached text of {doc.id} does not match its text_sha256")
    return data.decode("utf-8")


def load_run(runs_dir: Path, run_id: str) -> RunManifest:
    """A run's manifest; ValueError if there is no such run."""
    path = Path(runs_dir) / run_id / MANIFEST
    if not path.exists():
        raise ValueError(f"no run {run_id!r} in {runs_dir}")
    return RunManifest.model_validate_json(path.read_text(encoding="utf-8"))


def load_run_tags(runs_dir: Path, run_id: str) -> list[ValueTag]:
    """A run's tags (none yet if it has no tags file)."""
    path = Path(runs_dir) / run_id / TAGS
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ValueTag.model_validate_json(x) for x in lines if x.strip()]
