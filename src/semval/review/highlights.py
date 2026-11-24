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


# Palette slots that look alike side by side (orange/brown, gold/olive, teal/sky,
# red/magenta): once one is used in an article, the other is avoided while others are free.
LOOKALIKES: dict[int, int] = {1: 9, 9: 1, 2: 10, 10: 2, 4: 5, 5: 4, 0: 8, 8: 0}


def value_color(value_id: str) -> int:
    """A value's preferred palette slot: a stable hash, the same in every article."""
    return zlib.crc32(value_id.encode("utf-8")) % PALETTE_SIZE


def assign_colors(value_ids: Sequence[str]) -> dict[str, int]:
    """Palette slots for one article's values, in table order.

    Each value takes its preferred slot if that is free, else the next free slot after it,
    skipping look-alikes of used slots while other slots are free. After all
    ``PALETTE_SIZE`` slots are used, a new round starts (colours repeat).
    """
    out: dict[str, int] = {}
    used: set[int] = set()
    for vid in dict.fromkeys(value_ids):
        if len(used) == PALETTE_SIZE:
            used = set()
        avoid = used | {LOOKALIKES[c] for c in used if c in LOOKALIKES}
        pref = value_color(vid)
        ring = [(pref + i) % PALETTE_SIZE for i in range(PALETTE_SIZE)]
        slot = next((c for c in ring if c not in avoid), None)
        if slot is None:
            slot = next(c for c in ring if c not in used)
        used.add(slot)
        out[vid] = slot
    return out


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
