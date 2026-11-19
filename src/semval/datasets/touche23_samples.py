"""Touché23 items (English test split, Greek proxy) as ordinary samples for the tagging runner.

Each item becomes a ``Document`` whose text is ``ToucheItem.text`` (the same rendering the
few-shot examples and the review provider use). Texts go to the git-ignored raw cache; the
committed YAML holds ids and hashes. Samples have no collection window or request count:
``since``/``until`` stay None, ``per_country`` and ``requests`` 0.
"""

import hashlib
import random
from pathlib import Path
from typing import Final

from semval.datasets.touche23 import (
    DEFAULT_DIR,
    Split,
    ToucheItem,
    gold_at_level,
    load_proxy,
    load_split,
)
from semval.sampling.sample import (
    DEFAULT_RAW_DIR,
    DEFAULT_SAMPLES_DIR,
    SampleManifest,
    doc_text_path,
    write_manifest,
)
from semval.units import Document
from semval.values import Framework

EN_PREFIX: Final = "touche23-en"
EL_PREFIX: Final = "touche23-el"
NO_COUNTRY: Final = "ZZ"  # ISO 3166 user-assigned: the items belong to no country
GENRE: Final = "argument"
ZENODO_URL: Final = "https://zenodo.org/record/7879430"
_ALL_SPLITS: Final[tuple[Split, ...]] = ("train", "validation", "test")


def _prefix(language: str) -> str:
    return EL_PREFIX if language == "el" else EN_PREFIX


def _item_id(document_id: str) -> str:
    return document_id.split(":", 1)[1]


def _pick(items: list[ToucheItem], proxy_ids: set[str], n: int, seed: int) -> list[ToucheItem]:
    """All items with an id in ``proxy_ids``, then seeded sampling up to ``n``; sorted by id."""
    items = sorted(items, key=lambda i: i.id)
    must = [i for i in items if i.id in proxy_ids]
    if len(must) > n:
        raise ValueError(f"n={n} is below the {len(must)} proxy items that must be included")
    rest = [i for i in items if i.id not in proxy_ids]
    chosen = must + random.Random(seed).sample(rest, min(n - len(must), len(rest)))
    return sorted(chosen, key=lambda i: i.id)


def make_touche_sample(
    name: str,
    split: Split = "test",
    n: int = 300,
    seed: int = 1,
    proxy: bool = False,
    data_dir: Path = DEFAULT_DIR,
    samples_dir: Path = DEFAULT_SAMPLES_DIR,
    raw_dir: Path = DEFAULT_RAW_DIR,
) -> Path:
    """Write the sample YAML (and the texts) and return its path.

    English: ``n`` items of ``split``, always including every proxy item. ``proxy``: exactly
    the Greek proxy items.
    """
    proxy_items = load_proxy(data_dir)
    if proxy:
        items = sorted(proxy_items, key=lambda i: i.id)
    else:
        items = _pick(load_split(split, data_dir), {i.id for i in proxy_items}, n, seed)
    docs = []
    for item in items:
        prefix = _prefix(item.language)
        doc_id = f"{prefix}:{item.id}"
        data = item.text.encode("utf-8")
        path = doc_text_path(raw_dir, doc_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        docs.append(
            Document(
                id=doc_id,
                source_id=prefix,
                country=NO_COUNTRY,
                language=item.language,
                genre=GENRE,
                url=ZENODO_URL,
                text_sha256=hashlib.sha256(data).hexdigest(),
            )
        )
    manifest = SampleManifest(name=name, stats={}, documents=docs)
    return write_manifest(manifest, samples_dir)


def touche_gold(
    sample: SampleManifest, framework: Framework, level_id: str, data_dir: Path = DEFAULT_DIR
) -> dict[str, set[str]]:
    """Document id -> gold value ids at ``level_id``. A proxy document has its English twin's labels."""
    labelled: dict[str, ToucheItem] = {}
    for split in _ALL_SPLITS:
        try:
            labelled.update({i.id: i for i in load_split(split, data_dir)})
        except FileNotFoundError:
            continue  # a split that was not downloaded
    out = {}
    for doc in sample.documents:
        item = labelled.get(_item_id(doc.id))
        if item is None:
            raise ValueError(f"{doc.id}: no Touché23 item with that id in {data_dir}")
        out[doc.id] = gold_at_level(item, framework, level_id)
    return out
