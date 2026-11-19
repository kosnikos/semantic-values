"""Turn a model's verbatim quotes into character offsets in the document."""

from semval.tags import EvidenceSpan
from semval.units import Segment


def _collapse(s: str) -> tuple[str, list[int]]:
    """``s`` with each whitespace run made one space, and the original index of each char."""
    out: list[str] = []
    index: list[int] = []
    in_space = False
    for i, ch in enumerate(s):
        if ch.isspace():
            if in_space:
                continue
            out.append(" ")
            in_space = True
        else:
            out.append(ch)
            in_space = False
        index.append(i)
    return "".join(out), index


def _find(piece: str, quote: str) -> tuple[int, int] | None:
    """Span of ``quote`` in ``piece``: exact first, then with whitespace normalised."""
    if not quote.strip():
        return None
    pos = piece.find(quote)
    if pos >= 0:
        return pos, pos + len(quote)
    wanted = " ".join(quote.split())
    collapsed, index = _collapse(piece)
    pos = collapsed.find(wanted)
    if pos < 0:
        return None
    return index[pos], index[pos + len(wanted) - 1] + 1


def resolve_quotes(
    text: str, segment: Segment, quotes: list[str]
) -> tuple[list[EvidenceSpan], bool]:
    """Spans (document offsets) of ``quotes`` inside ``segment``; True if any is missing.

    A quote found more than once resolves to its first occurrence.
    """
    piece = text[segment.start : segment.end]
    spans: list[EvidenceSpan] = []
    unresolved = False
    for quote in quotes:
        found = _find(piece, quote)
        if found is None:
            unresolved = True
            continue
        span = EvidenceSpan(start=segment.start + found[0], end=segment.start + found[1])
        if span not in spans:
            spans.append(span)
    return spans, unresolved
