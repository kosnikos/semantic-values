"""Highlight geometry for the article: palette colours and text pieces under underlines.

Pure functions; the page only draws what these return.
"""

import itertools
import zlib
from collections.abc import Sequence

from semval.tags import EvidenceSpan

# Must match the --hl-<i> colours in static/review.css (test_palette_matches_css).
PALETTE_SIZE = 12
NO_LIMIT = 2**62  # "clip" spans to an unknown text length


def value_color(value_id: str) -> int:
    """A stable palette index for a value id, the same in every article and session."""
    return zlib.crc32(value_id.encode("utf-8")) % PALETTE_SIZE


def merged_spans(spans: Sequence[EvidenceSpan], length: int) -> list[tuple[int, int]]:
    """Spans clipped to the text and with overlaps joined, in text order."""
    out: list[list[int]] = []
    for s in sorted(spans, key=lambda e: (e.start, e.end)):
        a, b = max(0, s.start), min(length, s.end)
        if a >= b:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def text_pieces(text: str, marks_by_row: dict[int, list[tuple[int, int]]]) -> list[dict]:
    """Cut ``text`` at every mark boundary. Each piece lists ``[row, span, lane]`` for the
    marks covering it; a mark keeps one lane (underline depth) along its whole length."""
    marks = sorted(
        ((a, b, row, k) for row, spans in marks_by_row.items() for k, (a, b) in enumerate(spans)),
        key=lambda m: (m[0], -m[1]),
    )
    lane_end: list[int] = []
    laned = []
    for a, b, row, k in marks:
        lane = next((i for i, end in enumerate(lane_end) if end <= a), len(lane_end))
        if lane == len(lane_end):
            lane_end.append(b)
        lane_end[lane] = b
        laned.append((a, b, row, k, lane))
    bounds = sorted({0, len(text), *(m[0] for m in laned), *(m[1] for m in laned)})
    pieces = []
    for a, b in itertools.pairwise(bounds):
        cover = sorted(
            ([row, k, lane] for s, e, row, k, lane in laned if s <= a and e >= b),
            key=lambda m: m[2],
        )
        pieces.append({"t": text[a:b], "m": cover})
    return pieces
