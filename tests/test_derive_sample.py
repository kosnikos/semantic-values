from pathlib import Path

import pytest

from semval.sampling.sample import SampleManifest, derive_sample, write_manifest
from semval.units import Document


def _base() -> SampleManifest:
    docs = [
        Document(
            id=f"s:{i}", source_id="s", country="ZZ", language="en", genre="g", text_sha256="0"
        )
        for i in "abcd"
    ]
    return SampleManifest(
        name="base", since=None, until=None, per_country=0, requests=0, stats={}, documents=docs
    )


def test_derive_sample_keeps_order_and_rejects_unknown_id(tmp_path: Path) -> None:
    out = derive_sample(_base(), "sub", ["s:c", "s:a"])
    assert out.name == "sub" and [d.id for d in out.documents] == ["s:c", "s:a"]
    assert write_manifest(out, tmp_path).name == "sub.yaml"
    with pytest.raises(ValueError, match="s:zzz"):
        derive_sample(_base(), "sub", ["s:a", "s:zzz"])
