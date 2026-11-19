"""Per-source adapters. All source-specific parsing lives in this package."""

from semval.sampling.adapters.base import SourceAdapter
from semval.sampling.adapters.conversation import Conversation
from semval.sampling.adapters.efsyn import Efsyn
from semval.sampling.adapters.guardian import Guardian
from semval.sampling.adapters.standard import Standard
from semval.sampling.adapters.tanea import TaNea
from semval.sampling.adapters.tovima import ToVima

ADAPTERS: dict[str, SourceAdapter] = {
    a.source_id: a for a in (ToVima(), TaNea(), Efsyn(), Guardian(), Standard(), Conversation())
}
