"""saturation-meter — thematic saturation estimation for qualitative research."""

from .core import analyze_saturation, saturation_summary
from .models import InterviewEntry, SaturationPoint, SaturationReport

__all__ = [
    "analyze_saturation",
    "saturation_summary",
    "InterviewEntry",
    "SaturationPoint",
    "SaturationReport",
]
