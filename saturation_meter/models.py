"""Core dataclasses for saturation-meter."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InterviewEntry:
    """A single coded interview — one row in your dataset."""

    participant_id: str
    codes: list[str]

    def __post_init__(self) -> None:
        # Normalise on creation: strip whitespace, lowercase, deduplicate
        seen: set[str] = set()
        cleaned: list[str] = []
        for c in self.codes:
            norm = c.strip().lower()
            if norm and norm not in seen:
                seen.add(norm)
                cleaned.append(norm)
        self.codes = cleaned


@dataclass
class SaturationPoint:
    """Saturation metrics computed for a single interview in sequence."""

    interview_index: int            # 1-based position in the sequence
    participant_id: str
    new_themes_count: int           # themes not seen in any prior interview
    cumulative_themes_count: int    # total unique themes up to and including this interview
    new_theme_rate: float           # new_themes / cumulative_themes
    marginal_discovery_rate: float  # new_themes / first_interview_new_themes  (1.0 for idx 0)


@dataclass
class SaturationReport:
    """Full output from a saturation analysis run."""

    total_interviews: int
    total_unique_themes: int
    all_themes: list[str]                       # sorted list of every unique code seen
    points: list[SaturationPoint]               # one per interview, in order

    estimated_saturation_index: Optional[int]   # 1-based index of first saturated interview
    estimated_saturation_participant: Optional[str]
    is_saturated: bool
    confidence: str                             # "high" | "medium" | "low" | "insufficient_data"
    stop_recommendation: str
    warnings: list[str] = field(default_factory=list)
    narrative: Optional[str] = None             # LLM-generated (community scaffolding)
