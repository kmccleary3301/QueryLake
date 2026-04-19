from __future__ import annotations

from enum import Enum


class EffectClass(str, Enum):
    """Bounded Phase 1A effect taxonomy.

    This intentionally matches the reduced set frozen in ADR 002.
    """

    PURE_DETERMINISTIC = "PureDeterministic"
    PURE_VERSIONED = "PureVersioned"
    EXTERNAL_READ_ONLY = "ExternalReadOnly"
    SIDE_CHANNEL_EMIT = "SideChannelEmit"
